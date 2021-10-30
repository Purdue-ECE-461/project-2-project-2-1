import sys

# Interpret and print out test results
if len(sys.argv) > 1:
    with open(sys.argv[1], "r") as testfile:
        output = testfile.readlines()
        # Find number of passed and failed tests
        summary_idx = output.index("=========================== short test summary info ============================\n") + 1
        while (output[summary_idx][0] != "="):
            summary_idx += 1
        summary_line = output[summary_idx].split()
        num_failed = int(summary_line[summary_line.index("failed,") - 1])
        num_passed = int(summary_line[summary_line.index("passed,") - 1])
        coverage_line = output[len(output) - 1].split()
        coverage = coverage_line[3]

        print("Total: " + str(num_failed + num_passed))
        print("Passed: " + str(num_passed))
        print("Coverage: " + coverage)
        print(str(num_passed) + "/" + str(num_failed + num_passed) + " test cases passed. " + coverage + " line coverage achieved.")
        print()
else:
    print("Missing argument for testing printer!")
    exit(1)

exit(0)
