from field_agent import FieldAgent
from spymaster import SpyMaster

sm = SpyMaster()
sm.run_random_round(out_file="results.txt")
ag = FieldAgent()
ag.load_results("results.txt")
ag.evaluate_hints("evaluation.txt")
