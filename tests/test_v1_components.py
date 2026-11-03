import importlib.util, os, tempfile, unittest
ROOT=os.path.dirname(os.path.dirname(__file__))
def load(name,path):
 s=importlib.util.spec_from_file_location(name,os.path.join(ROOT,path)); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
risk=load("v1risk","trader-risk/v1_gate.py"); sizing=load("v1size","trader-budget/v1_size.py"); setups=load("v1setups","trader-entry/v1_setups.py"); evidence=load("v1evidence","trader-timemachine/v1_evidence.py"); paper=load("v1paper","trader-broker/paper_execute.py")
CFG={"mode":"paper","paper":True,"live_trading_enabled":False,"risk_gate_bypass":False,"setups":["orb","20_day_breakout","vwap_ma_reclaim"],"closed_bars_only":True,"min_reward_risk":1.5,"max_loss_per_trade_usd":125,"account_equity_usd":25000,"max_position_pct":20,"max_daily_loss_usd":375,"max_weekly_loss_pct":4,"max_trades_per_day":4,"max_consecutive_losses":3,"no_entries_before":"09:35","no_entries_after":"15:30"}
class V1(unittest.TestCase):
 def ticket(self):return {"side":"buy","setup":"orb","bar_closed":True,"entry":100,"stop":99,"target":101.5,"position_size":50}
 def test_pass(self): self.assertEqual(risk.evaluate(self.ticket(),CFG,{},__import__('datetime').datetime(2026,10,19,10,0))["verdict"],"PASS")
 def test_three_losses_block(self): self.assertEqual(risk.evaluate(self.ticket(),CFG,{"consecutive_losses":3},__import__('datetime').datetime(2026,10,19,10,0))["verdict"],"BLOCK")
 def test_closed_bar_required(self):
  t=self.ticket();t["bar_closed"]=False;self.assertEqual(risk.evaluate(t,CFG,{},__import__('datetime').datetime(2026,10,19,10,0))["verdict"],"BLOCK")
 def test_sizing(self): self.assertEqual(sizing.size(100,99)["qty"],50) # 20% position cap binds
 def test_setup(self): self.assertTrue(setups.build("AAPL","orb",{"open":100,"high":102,"low":99,"close":101,"closed":True},{"opening_range_high":100.5,"opening_range_low":99})["confirmed"])
 def test_evidence(self): self.assertEqual(evidence.summarize([{"r":1,"outcome":"target_first"},{"r":-1,"outcome":"stop_first"}])["sample_size"],2)
 def test_paper_refuses_block(self):
  with self.assertRaises(ValueError): paper.execute(self.ticket(),{"verdict":"BLOCK"},True,os.path.join(tempfile.gettempdir(),"never.json"))
 def test_paper_requires_approval(self):
  with self.assertRaises(ValueError): paper.execute(self.ticket(),{"verdict":"PASS"},False,os.path.join(tempfile.gettempdir(),"never.json"))
if __name__=="__main__": unittest.main()
