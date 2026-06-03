rm -r conjure-output
rm fl-test.solutions
conjure solve fl.essence test.param --number-of-solutions=all --solutions-in-one-file
grep Solution fl-test.solutions