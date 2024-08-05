import time

zeros = 10

sleeps = []

accusleep = lambda ms: 1 if ms > 11 else [x for x in range(ms*3)]

for x in range(zeros):
    sleeps.append(
        float("0.{}1".format("0"*x))
    )

for slp in sleeps:
    a = time.time_ns()
    time.sleep(slp)
    b = time.time_ns() - a

    print("REQ: {} | ACTUAL: {}".format(slp*1e+9, b))


print("-*" * 30)

targetMS = 1

a = time.time_ns()
accusleep(targetMS)
b = time.time_ns() - a

print("REQ: {} | ACTUAL: {}".format(targetMS, b/1000))