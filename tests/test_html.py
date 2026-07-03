"""Integration test: validates v5 APP mode + xvideos."""
import json, re, sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import tg_core as mod, generate_html, xv_spider

class TestGenerateHtml(unittest.TestCase):
    def setUp(self):
        self.od, self.oc = mod.DOWNLOAD_DIR, mod.CHANNELS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        mod.DOWNLOAD_DIR = Path(self.tmpdir.name)
        generate_html.XV_VIDEOS_FILE = mod.DOWNLOAD_DIR / "xvideos" / "videos.jsonl"
        for ch_id in ("ai_guoman","ciyuanb","llcosfc","dashijian"):
            (mod.DOWNLOAD_DIR/ch_id/"photo").mkdir(parents=True,exist_ok=True)
            (mod.DOWNLOAD_DIR/ch_id/"video").mkdir(parents=True,exist_ok=True)
        (mod.DOWNLOAD_DIR/"ai_guoman"/"photo"/"t.jpg").write_text("")
        (mod.DOWNLOAD_DIR/"ai_guoman"/"video"/"t.mp4").write_text("")
        (mod.DOWNLOAD_DIR/"dashijian"/"messages.jsonl").write_text(
            json.dumps({"id":1,"date":"2025-07-01T12:00:00","text":"T","channel":"d","media":[{"type":"photo","path":"photo/t.jpg"}]},ensure_ascii=False)+"\n",encoding="utf-8")
        self._tc = self.tmpdir.name+"/_c.json"
        mod.CHANNELS_FILE = Path(self._tc)
        Path(self._tc).write_text(json.dumps({"channels":[
            {"id":"ai_guoman","username":"A","name":"Men","mode":"text","group":"mens_fantasy","fetch_limit":50},
            {"id":"dashijian","username":"D","name":"News","mode":"text","fetch_limit":50},
        ]},ensure_ascii=False),encoding="utf-8")
    def tearDown(self):
        mod.DOWNLOAD_DIR, mod.CHANNELS_FILE = self.od, self.oc
        self.tmpdir.cleanup()
    def _html(self):
        generate_html.generate()
        return (mod.DOWNLOAD_DIR/"index.html").read_text(encoding="utf-8")
    def _data(self,html):
        m=re.search(r"window\.__DATA__\s*=\s*(\{.*?\});",html,re.DOTALL)
        return json.loads(m.group(1)) if m else {}

    def test_generated(self): self.assertIsNotNone(generate_html.generate())
    def test_tabs(self): h=self._html();self.assertIn("Men",h);self.assertIn("News",h)
    def test_app(self): h=self._html();self.assertIn("app-shell",h);self.assertIn("bottom-nav",h);self.assertIn("nav-item",h)
    def test_valid(self): h=self._html();self.assertTrue(h.startswith("<!DOCTYPE html>"));self.assertIn("</html>",h)
    def test_lightbox(self): h=self._html();self.assertIn("lightbox",h);self.assertIn("lb-close",h)
    def test_pagination(self): h=self._html();self.assertIn("pagination",h);self.assertIn("page-btn",h)
    def test_group(self): d=self._data(self._html());self.assertIn("mens_fantasy",d)
    def test_card_json(self):
        d=self._data(self._html())
        for t in d.values():
            for m in t.get("messages",[]):self.assertIn("id",m);self.assertIn("date",m);self.assertIn("channel",m)

class TestXvHtml(unittest.TestCase):
    def setUp(self):
        self.od, self.oc, self.ox = mod.DOWNLOAD_DIR, mod.CHANNELS_FILE, generate_html.XV_VIDEOS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        mod.DOWNLOAD_DIR = Path(self.tmpdir.name)
        xf = mod.DOWNLOAD_DIR/"xvideos"/"videos.jsonl"
        (mod.DOWNLOAD_DIR/"xvideos").mkdir(parents=True,exist_ok=True)
        generate_html.XV_VIDEOS_FILE = xf
        for ch_id in ("ai_guoman","ciyuanb","llcosfc","dashijian"):
            (mod.DOWNLOAD_DIR/ch_id/"photo").mkdir(parents=True,exist_ok=True)
            (mod.DOWNLOAD_DIR/ch_id/"video").mkdir(parents=True,exist_ok=True)
        (mod.DOWNLOAD_DIR/"dashijian"/"messages.jsonl").write_text(
            json.dumps({"id":1,"date":"2025-07-01T12:00:00","text":"T","channel":"d","media":[{"type":"photo","path":"photo/t.jpg"}]},ensure_ascii=False)+"\n",encoding="utf-8")
        self._tc = self.tmpdir.name+"/_c.json"
        mod.CHANNELS_FILE = Path(self._tc)
        Path(self._tc).write_text(json.dumps({"channels":[
            {"id":"ai_guoman","username":"A","name":"MF","mode":"text","group":"mens_fantasy","fetch_limit":50},
            {"id":"dashijian","username":"D","name":"News","mode":"text","fetch_limit":50},
        ]},ensure_ascii=False),encoding="utf-8")
        xf.write_text("\n".join(json.dumps(v,ensure_ascii=False) for v in [
            {"eid":"e1","video_id":1,"title":"T1","duration":"10m","views":"1k","uploader":"U1","thumbnail":"//t/1.jpg","quality":"1080p","tags":["內衣絲襪"],"fetched_at":"2026-07-03T12:00:00"},
            {"eid":"e2","video_id":2,"title":"T2","duration":"20m","views":"2k","uploader":"U2","thumbnail":"//t/2.jpg","quality":"720p","tags":["日本"],"fetched_at":"2026-07-03T11:00:00"},
        ]),encoding="utf-8")
    def tearDown(self):
        mod.DOWNLOAD_DIR, mod.CHANNELS_FILE, generate_html.XV_VIDEOS_FILE = self.od, self.oc, self.ox
        self.tmpdir.cleanup()
    def _html(self):
        generate_html.generate()
        return (mod.DOWNLOAD_DIR/"index.html").read_text(encoding="utf-8")

    def test_xv_tab(self): h=self._html();self.assertIn("弟兄們",h);self.assertIn("content-xvideos",h)
    def test_xv_data(self):
        h=self._html();self.assertIn("__XV_DATA__",h)
        m=re.search(r"window\.__XV_DATA__\s*=\s*(\{.*?\});",h,re.DOTALL);self.assertIsNotNone(m)
        self.assertEqual(json.loads(m.group(1))["videos"][0]["eid"],"e1")
    def test_tag_bar(self): h=self._html();self.assertIn("tag-bar",h);self.assertIn("內衣絲襪",h)
    def test_xv_embed(self): h=self._html();self.assertIn("xv-embed",h);self.assertIn("data-eid",h)
    def test_xv_pag(self): h=self._html();self.assertIn("pagination-xvideos",h)

if __name__=="__main__":unittest.main()
