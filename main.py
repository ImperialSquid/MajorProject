from field_operative import FieldOperative
from spymaster import SpyMaster

sm = SpyMaster()
sm.run_random_round(out_file="results.txt")
ag = FieldOperative()
ag.load_results_from_file("results.txt")
ag.evaluate_hints_to_file("evaluation.txt")
