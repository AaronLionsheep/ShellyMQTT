def main():
    build_code = 0
    build_code_file_name = "ShellyMQTT.indigoPlugin/Contents/Server Plugin/build_code.txt"

    with open(build_code_file_name) as build_code_file:
        data = build_code_file.read()
        if data:
            build_code = int(data, 16)

    with open(build_code_file_name, 'w') as build_code_file:
        build_code_file.write(hex(build_code + 1))


if __name__ == "__main__":
    main()
