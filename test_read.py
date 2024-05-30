import reader

file_list = ["wav/output/testchars_45.wav", "wav/output/HELLO_45.wav", "wav/output/ryryry.wav"]

test_reader = reader.TDDReader(45)

out_file = open("testout.txt", "w")

for file in file_list:
    out_file.write(file + ":\n")
    data = test_reader.decode_file(file)
    out_file.write(data + "\n")
print("done")