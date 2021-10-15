#!/usr/bin/python3

import subprocess
import tempfile
import hashlib
import argparse
import zipfile
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.hashes import Hash, SHA256
from cryptography.hazmat.primitives.serialization import PublicFormat, Encoding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

import bundle_pb2 as types


SIGNING_ALGORITHM = ec.ECDSA(SHA256())
SIGNING_PREFIX = b'twlo-mv-manifest-v1\0'

SIZE_OF_USER_FLASH = 0x100000


def hash(data):
    h = Hash(SHA256(), backend=default_backend())
    h.update(data)
    return h.finalize()


def hash_of_flash(area_size, contents):
    assert len(contents) < area_size, 'contents too big for flash area'
    image = contents + (b'\xff' * (area_size - len(contents)))
    return hash(image)


def key_id(type, pubkey):
    h = Hash(backend=default_backend(), algorithm=SHA256())
    h.update(type)
    h.update(pubkey)
    return int(h.finalize()[:8].hex(), 16)


def encode_public_key(pubkey):
    return pubkey.public_bytes(
        encoding=Encoding.X962,
        format=PublicFormat.UncompressedPoint)


def signing_key_id(pubkey):
    return key_id(b'\x00\x00', encode_public_key(pubkey))


def encode_signature(sig):
    r, s = decode_dss_signature(sig)
    return bytes.fromhex(('%064x%064x' % (r, s)))


def load_public_key(file):
    return serialization.load_pem_public_key(
        file.read(), backend=default_backend())


def load_private_key(file):
    return serialization.load_pem_private_key(
        file.read(), password=None, backend=default_backend())


def elf_to_rom(elf_filename):
    with tempfile.NamedTemporaryFile() as tmp:
        normalized_file = os.path.abspath(elf_filename)
        subprocess.check_call(['arm-none-eabi-objcopy', '-Obinary', '--gap-fill=0xff'] +
                              [normalized_file, tmp.name])

        tmp.seek(0)
        return tmp.read()


def write_layer(zip, contents):
    with zip.open(hash(contents).hex(), 'w') as f:
        f.write(contents)


def sign_manifest_or_not(args, manifest):
    if args.unsigned:
        manifest.signer_id = 0
        manifest.signature = b''
    else:
        signing_key = load_private_key(args.signing_key)
        manifest.signer_id = signing_key_id(signing_key.public_key())
        manifest.signature = encode_signature(
            signing_key.sign(SIGNING_PREFIX + manifest.body, SIGNING_ALGORITHM))


def _bundle_app(args):
    body = types.AppManifest.AppBody()
    body.debug.debuggable = args.debuggable

    if args.debug_auth_key:
        public_key = serialization.load_pem_public_key(
            args.debug_auth_key.read(),
            backend=default_backend())
        body.debug.debug_auth_pubkey = encode_public_key(public_key)

    body.update.maximum_politeness_time_sec = args.maximum_politeness_time
    body.update.minimum_kernel_version = args.minimum_kernel_version

    body.connectivity.connection_grace_time_sec = args.connection_grace_time
    body.connectivity.minimum_check_in_time_sec = args.minimum_check_in_time

    body.crash.minimum_restart_ms = args.minimum_restart_interval
    body.crash.maximum_restart_ms = args.maximum_restart_interval

    if args.crash_report_key:
        public_key = load_public_key(args.crash_report_key)
        body.crash.crash_report_pubkey = encode_public_key(public_key)
        body.crash.include_stack_bytes = args.crash_stack_bytes

    rom = elf_to_rom(args.elf.name)

    layer = body.layers.add()
    layer.target.internal_flash.start = 0
    layer.target.internal_flash.size = SIZE_OF_USER_FLASH
    layer.fetch_hash = hash(rom)
    layer.measurement_hash = hash_of_flash(SIZE_OF_USER_FLASH, rom)

    manifest = types.OpaqueManifest()
    manifest.body = body.SerializeToString()
    sign_manifest_or_not(args, manifest)

    # write layer contents and manifest into zip
    with zipfile.ZipFile(args.out, mode='w',
                         compression=zipfile.ZIP_DEFLATED) as zip:
        write_layer(zip, rom)

        with zip.open('manifest', 'w') as mf:
            mf.write(manifest.SerializeToString())

        print("Bundle written to file: %s" % args.out.name)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='command')

    # A note on 'SUPPRESS'ed options below - these are present for future expansion and
    # will be documented over the course of the Microvisor Beta period.  Please
    # refer to future documentation on the availability and use of these parameters.

    app = sp.add_parser('bundle-app')
    app.add_argument('elf', type=argparse.FileType('r'),
                     help='Input file containing ELF image to write at start of flash.')
    app.add_argument('out', type=argparse.FileType('wb'),
                     help='Output file for bundle zip.')

    def add_signing_opts(parser):
        group = parser.add_argument_group('Signing') \
            .add_mutually_exclusive_group(required=True)
        group.add_argument('--unsigned', action='store_true',
                           help='Do not sign manifest.')
        group.add_argument('--signing-key', type=argparse.FileType('rb'),
                           #help='Sign manifest using provided private key.')
                           help=argparse.SUPPRESS)

    add_signing_opts(app)

    group = app.add_argument_group('Debugging')
    group.add_argument('--disable-debugging', action='store_false',
                       dest='debuggable', default=True,
                       #help='Disable OTA debugging')
                       help=argparse.SUPPRESS)
    group.add_argument('--debug-auth-key', metavar='FILE',
                       type=argparse.FileType('rb'),
                       #help='OTA debugging is authenticated using public key in FILE.')
                       help=argparse.SUPPRESS)

    group = app.add_argument_group('Crash behaviour')
    group.add_argument('--crash-report-key', metavar='FILE',
                       type=argparse.FileType('rb'),
                       #help='Have device encrypt crash reports using public key in FILE.')
                       help=argparse.SUPPRESS)
    group.add_argument('--crash-stack-bytes', metavar='BYTES',
                       type=int, default=0,
                       #help='Include BYTES of crashing stack in crash report (default: none)')
                       help=argparse.SUPPRESS)
    group.add_argument('--minimum-restart-interval', metavar='MILLISECS',
                       type=int, default=0,
                       #help='Ensure crashing application is not automatically restarted more often than MILLISECS.')
                       help=argparse.SUPPRESS)
    group.add_argument('--maximum-restart-interval', metavar='MILLISECS',
                       type=int, default=0,
                       #help='Ensure repeatedly crashing application is restarted more often than every MILLISECS.')
                       help=argparse.SUPPRESS)

    group = app.add_argument_group('Update behaviour')
    group.add_argument('--maximum-politeness-time', metavar='SECS',
                       type=int, default=0,
                       #help='Take updates automatically after SECS wait if application does not respond.')
                       help=argparse.SUPPRESS)
    group.add_argument('--minimum-kernel-version', metavar='VERSION',
                       type=int, default=0,
                       help='Require minimum kernel version VERSION.')

    group = app.add_argument_group('Connection behaviour')
    group.add_argument('--connection-grace-time', metavar='SECS',
                       type=int, default=0,
                       help='Set connection grace time to SECS.')
    group.add_argument('--minimum-check-in-time', metavar='SECS',
                       type=int, default=0,
                       help='Have device autonomously reconnect to check for updates every SECS. '
                       'Default 0, which means to try to constantly stay connected.')

    args = ap.parse_args()

    if args.command == 'bundle-app':
        _bundle_app(args)
    else:
        ap.error('unknown command')
