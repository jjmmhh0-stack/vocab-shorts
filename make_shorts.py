import os, asyncio, subprocess
import edge_tts

TITLE = os.environ.get("SHORTS_TITLE", "하루 10초 필수 영단어")
WORD = os.environ.get("SHORTS_WORD", "inevitable")
MEANING = os.environ.get("SHORTS_MEANING", "피할 수 없는, 필연적인")
EXAMPLE = os.environ.get("SHORTS_EXAMPLE", "Change is inevitable.")
EXAMPLE_KO = os.environ.get("SHORTS_EXAMPLE_KO", "변화는 피할 수 없다.")

VOICE_EN = "en-US-JennyNeural"
VOICE_KO = "ko-KR-SunHiNeural"

async def generate_tts(text, voice, raw_file, final_file, rate="+5%", end_pad=0.18):
    await edge_tts.Communicate(text, voice, rate=rate, volume="+12%").save(raw_file)
    af = f"silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse,apad=pad_dur={end_pad}"
    subprocess.run(["ffmpeg", "-y", "-i", raw_file, "-af", af, "-c:a", "libmp3lame", "-q:a", "2", final_file], check=True)

def get_duration(filename):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename]
    return float(subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)

def wrap_text(text, max_chars=22):
    words, lines, current = text.split(), [], ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars: current = (current + " " + w).strip()
        else: lines.append(current); current = w
    if current: lines.append(current)
    return "\n".join(lines)

async def main():
    await generate_tts(f"{WORD}.", VOICE_EN, "w1_raw.mp3", "w1.mp3", rate="+0%", end_pad=0.25)
    await generate_tts(f"{MEANING}.", VOICE_KO, "m1_raw.mp3", "m1.mp3", rate="+12%", end_pad=0.25)
    await generate_tts(f"{WORD}.", VOICE_EN, "w2_raw.mp3", "w2.mp3", rate="-5%", end_pad=0.25)
    await generate_tts(f"{EXAMPLE}", VOICE_EN, "ex_raw.mp3", "ex.mp3", rate="+0%", end_pad=0.20)
    await generate_tts(f"{EXAMPLE_KO}", VOICE_KO, "exk_raw.mp3", "exk.mp3", rate="+12%", end_pad=0.25)
    await generate_tts("매일 한 단어씩 외우려면 구독과 좋아요 부탁드려요", VOICE_KO, "sub_raw.mp3", "sub.mp3", rate="+15%", end_pad=0.25)

    d_w1, d_m1, d_w2 = get_duration("w1.mp3"), get_duration("m1.mp3"), get_duration("w2.mp3")
    d_ex, d_exk, d_sub = get_duration("ex.mp3"), get_duration("exk.mp3"), get_duration("sub.mp3")

    t_meaning = d_w1
    t_example = d_w1 + d_m1 + d_w2
    t_sub = t_example + d_ex + d_exk
    total_dur = t_sub + d_sub

    with open("concat.txt", "w") as f:
        f.write("file 'w1.mp3'\nfile 'm1.mp3'\nfile 'w2.mp3'\nfile 'ex.mp3'\nfile 'exk.mp3'\nfile 'sub.mp3'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "raw_audio.mp3"], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", "raw_audio.mp3", "-filter:a", "loudnorm=I=-15:TP=-1.5:LRA=11", "full_audio.mp3"], check=True)

    font_path = next((p for p in ["/usr/share/fonts/truetype/nanum/NanumSquareRoundEB.ttf", "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"] if os.path.exists(p)), "")
    with open("title.txt", "w", encoding="utf-8") as f: f.write(TITLE.replace("#Shorts", "").replace("#영단어", "").strip()[:16])
    with open("word.txt", "w", encoding="utf-8") as f: f.write(WORD.strip())
    with open("meaning.txt", "w", encoding="utf-8") as f: f.write(wrap_text(MEANING, 13))
    with open("ex_en.txt", "w", encoding="utf-8") as f: f.write(wrap_text(EXAMPLE, 24))
    with open("ex_ko.txt", "w", encoding="utf-8") as f: f.write(wrap_text(EXAMPLE_KO, 16))
    with open("sub.txt", "w", encoding="utf-8") as f: f.write("매일 1단어! 구독 & 좋아요 부탁드려요!")

    vf = (
        f"drawbox=x=60:y=380:w=960:h=1120:color=#161B22@0.95:t=fill,"
        f"drawbox=x=60:y=380:w=960:h=1120:color=#30363D:t=4,"
        f"drawbox=x=80:y=200:w=920:h=125:color=#FFD600:t=fill,"
        f"drawtext=fontfile={font_path}:textfile=title.txt:fontcolor=#111111:fontsize=54:x=(w-text_w)/2:y=235,"
        f"drawtext=fontfile={font_path}:textfile=word.txt:fontcolor=#00E5FF:fontsize=115:borderw=5:bordercolor=black:x=(w-text_w)/2:y=460,"
        f"drawbox=x=110:y=640:w=860:h=210:color=#21262D:t=fill:enable='gte(t,{t_meaning})',"
        f"drawbox=x=110:y=640:w=860:h=210:color=#00E676:t=4:enable='gte(t,{t_meaning})',"
        f"drawtext=fontfile={font_path}:textfile=meaning.txt:fontcolor=#00E676:fontsize=76:borderw=4:bordercolor=black:x=(w-text_w)/2:y=695:line_spacing=18:enable='gte(t,{t_meaning})',"
        f"drawbox=x=100:y=910:w=880:h=520:color=#0D1117@0.85:t=fill:enable='gte(t,{t_example})',"
        f"drawbox=x=100:y=910:w=880:h=520:color=#FFD600:t=3:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_path}:text='EXAMPLE':fontcolor=#FFD600:fontsize=44:x=(w-text_w)/2:y=945:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_path}:textfile=ex_en.txt:fontcolor=white:fontsize=58:borderw=4:bordercolor=black:x=(w-text_w)/2:y=1030:line_spacing=18:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_path}:textfile=ex_ko.txt:fontcolor=#BDBDBD:fontsize=50:borderw=3:bordercolor=black:x=(w-text_w)/2:y=1240:line_spacing=16:enable='gte(t,{t_example})',"
        f"drawbox=x=80:y=1540:w=920:h=110:color=#FF1744@0.92:t=fill:enable='gte(t,{t_sub})',"
        f"drawtext=fontfile={font_path}:textfile=sub.txt:fontcolor=white:fontsize=46:borderw=3:bordercolor=black:x=(w-text_w)/2:y=1572:enable='gte(t,{t_sub})'"
    )
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=#0D1117:s=1080x1920:d={total_dur}",
        "-i", "full_audio.mp3",
        "-vf", vf,
        "-t", f"{total_dur}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        "output.mp4"
    ], check=True)
    print("여성 성우 영단어 쇼츠 렌더링 완료: output.mp4", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
