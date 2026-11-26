import os, asyncio, subprocess
from PIL import Image, ImageEnhance
import edge_tts

TITLE = os.environ.get("SHORTS_TITLE", "10초 영단어 #Shorts")
HOOK = os.environ.get("SHORTS_HOOK", "나한테 왜 이렇게 깐깐하게 구냐고 할 때")
WORD = os.environ.get("SHORTS_WORD", "nitpicky")
PRON = os.environ.get("SHORTS_PRON", "/ˈnɪtˌpɪki/  [ 닛피키 ]")
MEANING = os.environ.get("SHORTS_MEANING", "사소한 것에 얽매이는, 몹시 까다로운")
EXAMPLE = os.environ.get("SHORTS_EXAMPLE", "Don't be so nitpicky about small details.")
EXAMPLE_PRON = os.environ.get("SHORTS_EXAMPLE_PRON", "돈트 비 소 닛피키 어바웃 스몰 디테일즈")
EXAMPLE_KO = os.environ.get("SHORTS_EXAMPLE_KO", "작은 세부 사항까지 너무 까다롭게 굴지 마세요")

VOICE_EN = "en-US-JennyNeural"
VOICE_KO = "ko-KR-SunHiNeural"

async def generate_tts(text, voice, raw_file, final_file, rate="+8%", end_pad=0.15):
    await edge_tts.Communicate(text, voice, rate=rate, volume="+12%").save(raw_file)
    af = f"silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse,apad=pad_dur={end_pad}"
    subprocess.run(["ffmpeg", "-y", "-i", raw_file, "-af", af, "-c:a", "libmp3lame", "-q:a", "2", final_file], check=True)

def get_duration(filename):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename]
    return float(subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)

def wrap_text(text, max_chars=16, max_lines=3):
    words, lines, current = text.split(), [], ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current = (current + " " + w).strip()
        else:
            lines.append(current)
            current = w
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return "\n".join(lines)

def prepare_bg(out_path="final_bg.jpg"):
    for fname in ["bg.jpg", "bg.png", "bg.jpeg"]:
        if os.path.exists(fname):
            img = Image.open(fname).convert("RGB").resize((1080, 1920), Image.LANCZOS)
            ImageEnhance.Brightness(img).enhance(0.55).save(out_path, quality=92)
            print(f"사용자 배경 적용 완료: {fname}", flush=True)
            return
    Image.new("RGB", (1080, 1920), color=(15, 23, 42)).save(out_path)

async def main():
    prepare_bg("final_bg.jpg")
    await generate_tts(HOOK, VOICE_KO, "h_raw.mp3", "h.mp3", rate="+12%", end_pad=0.20)
    await generate_tts(f"{WORD}.", VOICE_EN, "w_raw.mp3", "w.mp3", rate="+0%", end_pad=0.20)
    await generate_tts(MEANING, VOICE_KO, "m_raw.mp3", "m.mp3", rate="+12%", end_pad=0.25)
    await generate_tts("문장 예시입니다.", VOICE_KO, "t_raw.mp3", "t.mp3", rate="+12%", end_pad=0.18)
    await generate_tts(EXAMPLE, VOICE_EN, "ex_raw.mp3", "ex.mp3", rate="+2%", end_pad=0.18)
    await generate_tts(EXAMPLE_KO, VOICE_KO, "exk_raw.mp3", "exk.mp3", rate="+12%", end_pad=0.30)

    d_h, d_w, d_m = get_duration("h.mp3"), get_duration("w.mp3"), get_duration("m.mp3")
    d_t, d_ex, d_exk = get_duration("t.mp3"), get_duration("ex.mp3"), get_duration("exk.mp3")

    t_word = d_h
    t_meaning = d_h + d_w
    t_example = d_h + d_w + d_m + d_t
    total_dur = t_example + d_ex + d_exk

    with open("concat.txt", "w") as f:
        f.write("file 'h.mp3'\nfile 'w.mp3'\nfile 'm.mp3'\nfile 't.mp3'\nfile 'ex.mp3'\nfile 'exk.mp3'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "raw_audio.mp3"], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", "raw_audio.mp3", "-filter:a", "loudnorm=I=-15:TP=-1.5:LRA=11", "full_audio.mp3"], check=True)

    font_ko = "/usr/share/fonts/truetype/nanum/NanumSquareRoundEB.ttf"
    if not os.path.exists(font_ko):
        font_ko = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
    font_ipa = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_ipa):
        font_ipa = font_ko

    ipa_part, kor_pron_part = PRON, ""
    if "[" in PRON:
        parts = PRON.split("[", 1)
        ipa_part = parts[0].strip()
        kor_pron_part = "[" + parts[1].strip()

    with open("hook.txt", "w", encoding="utf-8") as f: f.write(wrap_text(HOOK, 15, 3))
    with open("word.txt", "w", encoding="utf-8") as f: f.write(WORD.strip())
    with open("ipa.txt", "w", encoding="utf-8") as f: f.write(ipa_part)
    with open("kor_pron.txt", "w", encoding="utf-8") as f: f.write(kor_pron_part)
    with open("meaning.txt", "w", encoding="utf-8") as f: f.write(wrap_text(MEANING, 13, 2))
    with open("ex_en.txt", "w", encoding="utf-8") as f: f.write(wrap_text(EXAMPLE, 26, 2))
    with open("ex_pron.txt", "w", encoding="utf-8") as f: f.write(wrap_text(EXAMPLE_PRON, 20, 2))
    with open("ex_ko.txt", "w", encoding="utf-8") as f: f.write(wrap_text(EXAMPLE_KO, 17, 2))

    vf = (
        f"drawtext=fontfile={font_ko}:textfile=hook.txt:fontcolor=white:fontsize=58:borderw=6:bordercolor=black:x=(w-text_w)/2:y=150:line_spacing=16,"
        f"drawtext=fontfile={font_ko}:textfile=word.txt:fontcolor=#00E5FF:fontsize=120:borderw=8:bordercolor=black:x=(w-text_w)/2:y=480:enable='gte(t,{t_word})',"
        f"drawtext=fontfile={font_ipa}:textfile=ipa.txt:fontcolor=#E0E0E0:fontsize=44:borderw=4:bordercolor=black:x=(w-text_w)/2:y=630:enable='gte(t,{t_word})',"
        f"drawtext=fontfile={font_ko}:textfile=kor_pron.txt:fontcolor=#B2EBF2:fontsize=48:borderw=4:bordercolor=black:x=(w-text_w)/2:y=690:enable='gte(t,{t_word})',"
        f"drawtext=fontfile={font_ko}:textfile=meaning.txt:fontcolor=#FFD600:fontsize=72:borderw=7:bordercolor=black:x=(w-text_w)/2:y=780:line_spacing=18:enable='gte(t,{t_meaning})',"
        f"drawtext=fontfile={font_ko}:textfile=ex_en.txt:fontcolor=white:fontsize=56:borderw=6:bordercolor=black:x=(w-text_w)/2:y=1010:line_spacing=16:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_ko}:textfile=ex_pron.txt:fontcolor=#80D8FF:fontsize=44:borderw=4:bordercolor=black:x=(w-text_w)/2:y=1210:line_spacing=14:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_ko}:textfile=ex_ko.txt:fontcolor=#00E676:fontsize=52:borderw=5:bordercolor=black:x=(w-text_w)/2:y=1390:line_spacing=16:enable='gte(t,{t_example})'"
    )
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", "final_bg.jpg", "-i", "full_audio.mp3", "-vf", vf, "-t", f"{total_dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "output.mp4"], check=True)
    print("겹침 없는 영단어 쇼츠 렌더링 완료: output.mp4", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
