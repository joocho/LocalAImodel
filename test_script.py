test_sentences = [
    "The 7.62mm machine gun delivers a sustained rate of fire of 650 rounds per minute with an effective range of 800 meters.",
    "The weapon system features a quick-change barrel mechanism that enables continuous operation during extended engagements.",
    "Vehicle-mounted machine guns serve as secondary armament systems on armored personnel carriers and main battle tanks."
]

for i, sentence in enumerate(test_sentences, 1):
    print(f"\n=== Test {i} ===")
    print(f"EN: {sentence}")
    # 여기에 번역 결과 출력