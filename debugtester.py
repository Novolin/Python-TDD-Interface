import wavreadtext

test_files = ("wav/output/HELLO_45", "wav/output/HELLO_50", "wav/output/ryryry.wav")

test45 = wavreadtext.AudioReader(45)
test50 = wavreadtext.AudioReader(50)

testfile = input("Choose test file:")
test45.set_input_source("readtest_f.wav")
test50.set_input_source("read")