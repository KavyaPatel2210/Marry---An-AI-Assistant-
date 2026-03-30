import sys, os, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predict import predict_intent, get_response

TEST_CASES = [
    ("hello","greeting"),("hi there","greeting"),("good morning","greeting"),
    ("tell me about yourself","about_assistant"),("who are you","about_assistant"),
    ("help me","help_user"),("i need assistance","help_user"),
    ("thank you so much","thank_you"),("thanks buddy","thank_you"),
    ("sorry about that","apology"),
    ("tell me a joke","jokes_fun"),("make me laugh","jokes_fun"),
    ("motivate me","motivation"),("i feel lazy","motivation"),
    ("i am happy today","mood_happy"),("feeling amazing","mood_happy"),
    ("i am sad","mood_sad"),("i feel down","mood_sad"),
    ("how are you","small_talk"),("what are you doing","small_talk"),
    ("what can you do","capabilities"),("your features","capabilities"),
    ("what is ai","ai_knowledge"),("what is machine learning","ai_knowledge"),
    ("you are amazing","compliments"),("good job","compliments"),
    ("who made you","creator_info"),("who built you","creator_info"),
    ("what time is it","time"),("current time","time"),("time please","time"),
    ("play music","music"),("play bollywood songs","music"),("play a song","music"),
    ("weather today","weather"),("what is the weather","weather"),
    ("search google","search"),("search for python","search"),
    ("search wikipedia","wikipedia"),("open wikipedia","wikipedia"),
    ("open youtube","open_app"),("open calculator","open_app"),("open notepad","open_app"),
    ("open chrome","open_app"),("open instagram","open_app"),("open gmail","open_app"),
    ("order food","food"),("i am hungry","food"),("open zomato","food"),
    ("open amazon","shopping"),("open flipkart","shopping"),
    ("bye","exit"),("goodbye","exit"),("quit","exit"),
]

TAGS = [
    "greeting","about_assistant","help_user","thank_you","apology",
    "jokes_fun","motivation","mood_happy","mood_sad","small_talk",
    "capabilities","ai_knowledge","compliments","creator_info",
    "music","weather","time","search","open_app","wikipedia",
    "food","shopping","exit"
]

# ── TEST 1: ML Model ──────────────────────────────────────────────────
print("\n" + "="*90)
print("  TEST 1 — ML Model: predict_intent() for all 53 test inputs")
print("="*90)
print(f"  {'INPUT':<35} {'EXPECTED':<20} {'GOT':<20} {'CONF':>6}  RESULT")
print("  " + "-"*85)

passed = 0
failed = 0
fails = []

for text, expected in TEST_CASES:
    tag, conf = predict_intent(text)
    ok = (tag == expected)
    passed += ok
    failed += (not ok)
    if not ok:
        fails.append((text, expected, tag, conf))
    result = "PASS" if ok else "FAIL ***"
    print(f"  {text:<35} {expected:<20} {tag:<20} {conf*100:>5.1f}%  {result}")

print(f"\n  ML Model Score: {passed}/{passed+failed} passed, {failed} failed")

if fails:
    print("\n  FAILED CASES:")
    for t, e, g, c in fails:
        print(f"    Input: {t!r:35} Expected: {e}, Got: {g} ({c*100:.1f}%)")

# ── TEST 2: Response Coverage ─────────────────────────────────────────
print("\n" + "="*90)
print("  TEST 2 — Response Coverage: get_response() for all 23 tags")
print("="*90)
print(f"  {'TAG':<25} {'STATUS':<8} SAMPLE RESPONSE")
print("  " + "-"*85)

resp_ok = 0
for tag in TAGS:
    resp = get_response(tag)
    ok = bool(resp) and "understand" not in resp
    resp_ok += ok
    status = "OK" if ok else "MISSING"
    print(f"  {tag:<25} {status:<8} {resp[:55]}")

print(f"\n  Response Coverage: {resp_ok}/{len(TAGS)} tags have valid responses")

# ── TEST 3: Django API ────────────────────────────────────────────────
print("\n" + "="*90)
print("  TEST 3 — Django API: POST /send_command/")
print("="*90)

API_SAMPLES = [
    "hello", "what time is it", "tell me a joke",
    "thank you", "motivate me", "what is ai",
    "you are amazing", "i am sad"
]

api_pass = 0
api_fail = 0

try:
    urllib.request.urlopen("http://127.0.0.1:8000/", timeout=3)
    server_up = True
    print("  Server reachable at http://127.0.0.1:8000\n")
except Exception as e:
    server_up = False
    print(f"  Server NOT reachable: {e}")
    print("  Skipping API test.\n")

if server_up:
    print(f"  {'COMMAND':<35} {'HTTP':>4}  SERVER RESPONSE")
    print("  " + "-"*75)
    for cmd in API_SAMPLES:
        try:
            payload = json.dumps({"command": cmd}).encode("utf-8")
            req = urllib.request.Request(
                "http://127.0.0.1:8000/send_command/",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                body = json.loads(resp.read().decode())
                msg = body.get("message", str(body))[:50]
                print(f"  {cmd:<35} {code:>4}  {msg}")
                api_pass += 1
        except urllib.error.HTTPError as e:
            print(f"  {cmd:<35} {e.code:>4}  HTTP Error: {e.reason}")
            api_fail += 1
        except Exception as e:
            print(f"  {cmd:<35} {'ERR':>4}  {str(e)[:50]}")
            api_fail += 1

    print(f"\n  API Score: {api_pass}/{api_pass+api_fail} requests succeeded")

# ── FINAL SUMMARY ─────────────────────────────────────────────────────
print("\n" + "="*90)
print("  FINAL SUMMARY")
print("="*90)
print(f"  ML Model Accuracy  : {passed}/{passed+failed}  ({passed/(passed+failed)*100:.1f}%)")
print(f"  Response Coverage  : {resp_ok}/{len(TAGS)}  (all 23 intent tags)")
if server_up:
    print(f"  API Endpoint       : {api_pass}/{api_pass+api_fail}  requests OK")
else:
    print(f"  API Endpoint       : SKIPPED (server not running)")

overall = (passed + resp_ok + (api_pass if server_up else 0))
total   = ((passed+failed) + len(TAGS) + (api_pass+api_fail if server_up else 0))
print(f"\n  Overall Score      : {overall}/{total}  ({overall/total*100:.1f}%)")
print("="*90 + "\n")
