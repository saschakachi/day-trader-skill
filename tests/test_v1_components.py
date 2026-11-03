import importlib.util, os, tempfile, unittest, datetime
ROOT=os.path.dirname(os.path.dirname(__file__))
def load(name,path):
 s=importlib.util.spec_from_file_location(name,os.path.join(ROOT,path)); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
risk=load("v1risk","trader-risk/v1_gate.py"); sizing=load("v1size","trader-budget/v1_size.py"); setups=load("v1setups","trader-entry/v1_setups.py"); evidence=load("v1evidence","trader-timemachine/v1_evidence.py"); paper=load("v1paper","trader-broker/paper_execute.py")
CFG={"mode":"paper","paper":True,"live_trading_enabled":False,"risk_gate_bypass":False,"allow_short":False,"allow_margin":False,"allow_options":False,"setups":["orb","20_day_breakout","vwap_ma_reclaim"],"closed_bars_only":True,"min_reward_risk":1.5,"max_loss_per_trade_usd":125,"account_equity_usd":25000,"max_position_pct":20,"max_daily_loss_usd":375,"max_weekly_loss_pct":4,"max_trades_per_day":4,"max_consecutive_losses":3,"no_entries_before":"09:35","no_entries_after":"15:30"}
class V1(unittest.TestCase):
 def ticket(self):return {"side":"buy","setup":"orb","bar_closed":True,"entry":100,"stop":99,"target":101.5,"position_size":50}
 def pass_result(self,t=None): return risk.evaluate(t or self.ticket(),CFG,{},datetime.datetime(2026,10,19,10,0))
 def test_pass(self): self.assertEqual(self.pass_result()["verdict"],"PASS")
 def test_three_losses_block(self): self.assertEqual(risk.evaluate(self.ticket(),CFG,{"consecutive_losses":3},datetime.datetime(2026,10,19,10,0))["verdict"],"BLOCK")
 def test_daily_trade_limit(self): self.assertEqual(risk.evaluate(self.ticket(),CFG,{"trades_today":4},datetime.datetime(2026,10,19,10,0))["verdict"],"BLOCK")
 def test_daily_loss_limit(self): self.assertEqual(risk.evaluate(self.ticket(),CFG,{"daily_loss_usd":375},datetime.datetime(2026,10,19,10,0))["verdict"],"BLOCK")
 def test_weekly_loss_limit(self): self.assertEqual(risk.evaluate(self.ticket(),CFG,{"weekly_loss_usd":1000},datetime.datetime(2026,10,19,10,0))["verdict"],"BLOCK")
 def test_closed_bar_required(self):
  t=self.ticket();t["bar_closed"]=False;self.assertEqual(risk.evaluate(t,CFG,{},datetime.datetime(2026,10,19,10,0))["verdict"],"BLOCK")
 def test_rr_minimum(self):
  t=self.ticket();t["target"]=101;self.assertEqual(risk.evaluate(t,CFG,{},datetime.datetime(2026,10,19,10,0))["verdict"],"BLOCK")
 def test_position_cap(self):
  t=self.ticket();t["position_size"]=51;self.assertEqual(risk.evaluate(t,CFG,{},datetime.datetime(2026,10,19,10,0))["verdict"],"BLOCK")
 def test_after_entry_window(self): self.assertEqual(risk.evaluate(self.ticket(),CFG,{},datetime.datetime(2026,10,19,15,31))["verdict"],"BLOCK")
 def test_sizing(self): self.assertEqual(sizing.size(100,99)["qty"],50)
 def test_setup(self): self.assertTrue(setups.build("AAPL","orb",{"open":100,"high":102,"low":99,"close":101,"closed":True},{"opening_range_high":100.5,"opening_range_low":99})["confirmed"])
 def test_evidence(self): self.assertEqual(evidence.summarize([{"r":1,"outcome":"target_first"},{"r":-1,"outcome":"stop_first"}])["sample_size"],2)
 def test_paper_refuses_block(self):
  with self.assertRaises(ValueError): paper.execute(self.ticket(),{"verdict":"BLOCK"},True,os.path.join(tempfile.gettempdir(),"never.json"),CFG)
 def test_paper_requires_approval(self):
  with self.assertRaises(ValueError): paper.execute(self.ticket(),self.pass_result(),False,os.path.join(tempfile.gettempdir(),"never.json"),CFG)
 def test_paper_rejects_mismatched_risk(self):
  t=self.ticket(); r=self.pass_result(t); changed=dict(t); changed["entry"]=100.25
  with self.assertRaises(ValueError): paper.execute(changed,r,True,os.path.join(tempfile.gettempdir(),"never.json"),CFG)
 def test_paper_rejects_live_config(self):
  c=dict(CFG);c["live_trading_enabled"]=True
  with self.assertRaises(ValueError): paper.execute(self.ticket(),self.pass_result(),True,os.path.join(tempfile.gettempdir(),"never.json"),c)
if __name__=="__main__": unittest.main()
