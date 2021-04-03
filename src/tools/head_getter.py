heads_file = "../../assets/agent_heads.in.txt"
input = open(heads_file, "r")
out = open("../../assets/agent_heads.out.txt", "w")
lines = input.readlines()
heads = []
for line in lines:
    start = line.index('SkullOwner')
    block = line[start:-4]
    out.write(block+"\n")

input.close()
out.close()

