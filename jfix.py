#!/usr/bin/env python3
import argparse
import os
import sys
from json import decoder, loads
import logging

CONFIG = {
    'ACCEPT_FILES': '.json',
    'ESCAPE_CHARACTER': '\\',
    'FIX_ENABLED': False,
    'LOGGING_MODE': logging.INFO,
    'START_LOCATION': ''
}

FILES_DISCOVERED = []


def json_fixer(content, pos):
    problem_char = content[pos]
    updated_content = None

    if problem_char is '"':
        logging.info(f"Known char: [{problem_char}] - {pos} | Starting fix: adding {CONFIG['ESCAPE_CHARACTER']}")
        updated_content = content[:pos] + CONFIG['ESCAPE_CHARACTER'] + content[pos:]

    elif problem_char is ' ':
        logging.info(f"Known char: [{problem_char}] - {pos} | Starting fix: pos - 1")
        updated_content = json_fixer(content, pos-1)

    else:
        logging.error(f"[!] Unknown char | MSG: [{problem_char}] - {pos}")

    return updated_content


def json_validator(file_path):
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            content = f.read()

        fix_needed = False
        for i in content:  # iterations limited by content
            has_error = False

            try:
                loads(content)
            except decoder.JSONDecodeError as err:
                has_error = True
                fix_needed = True
                content = json_fixer(content, err.pos-1)

                if content is None:
                    fix_needed = False
                    logging.error(f"[!] error parsing file: {file_path}")
                    break

            if has_error is False:
                break

        if fix_needed is True:
            if CONFIG['FIX_ENABLED'] is False:
                logging.info(f"Fix disabled use --f flag to enable")
            else:
                with open(file_path, 'w') as f:
                    logging.info(f"Overriding file content: {file_path}")
                    f.write(content)


def directory_scanner(path):
    logging.debug(f"discovering files in: {path}")
    try:
        (dir_path, dir_names, file_name) = next(os.walk(path))
    except StopIteration as err:
        logging.critical(f"Iteration error, try narrower scope | Path: {path}")
        sys.exit(1)

    if dir_names:
        for d in dir_names:
            directory_scanner(os.path.join(dir_path, d))

    if file_name:
        for f in file_name:
            logging.debug(f"file discovered: {f}")
            FILES_DISCOVERED.append(os.path.join(dir_path, f))


def cmd_params():
    arg_parser = argparse.ArgumentParser(
        description="Simple broken *.json file fixer"
    )

    arg_parser.add_argument('--p', type=str, help='File location', default=CONFIG['START_LOCATION'])
    arg_parser.add_argument('--c', type=str, help='Custom escape character', default=CONFIG['ESCAPE_CHARACTER'])
    arg_parser.add_argument('--f', help='Enable fix mode', action='store_true')
    arg_parser.add_argument('--d', help='Enable debug logging', action='store_true')

    args = arg_parser.parse_args()
    CONFIG['START_LOCATION'] = args.p
    CONFIG['ESCAPE_CHARACTER'] = args.c
    CONFIG['FIX_ENABLED'] = args.f
    CONFIG['LOGGING_MODE'] = logging.DEBUG if args.d else CONFIG['LOGGING_MODE']


def main():
    cmd_params()
    logging.basicConfig(
        level=CONFIG['LOGGING_MODE'],
        format='[%(levelname)s] %(message)s'
    )
    directory_scanner(CONFIG['START_LOCATION'])

    for f in FILES_DISCOVERED:
        if CONFIG['ACCEPT_FILES'].casefold() in f[-len(CONFIG['ACCEPT_FILES'].casefold()):]:
            logging.debug(f"validating file: {f}")
            json_validator(f)
        else:
            logging.info(f"Unsupported file type: {f}")


if __name__ == "__main__":
    main()
