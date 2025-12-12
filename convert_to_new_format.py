#!/usr/bin/env python3
import re
from pathlib import Path

SKILL_RENAMES = {"Древковое": "Полэкс"}

def norm_bool(val: str) -> str:
    v = val.strip().lower()
    if v == "true": return "True"
    if v == "false": return "False"
    return val

def build_skill_lines(order, ranks, focuses, level, exp):
    lines = [
        "######### Skills data",
        "# NOTE : Hero level and raw XP",
        f"level={level or 1}",
        f"exp={exp or 0}",
        "autoCalculateGlobalXp=False",
        "useRealSkillXp=True",
    ]
    for name in order:
        new_name = SKILL_RENAMES.get(name, name)
        lines.append(f"skill.{new_name}={ranks.get(name, 0)}")
        lines.append(f"skill.focus.{new_name}={focuses.get(name, focuses.get(new_name, 0))}")
        lines.append(f"skill.xp.{new_name}=0")
    return lines

def build_perk_lines(perks):
    lines = ["", "######### Perks data"]
    for skill, perk, val in perks:
        skill = SKILL_RENAMES.get(skill, skill)
        lines.append(f"perk.{skill}.{perk}={'True' if val.strip()=='1' else 'False'}")
    return lines

def convert(path: Path):
    text = path.read_text(encoding="utf-8").splitlines()
    new_lines = []
    mode = "copy"
    skill_order, skill_ranks, skill_focuses = [], {}, {}
    perks = []
    level = exp = None

    for line in text:
        stripped = line.strip()

        if stripped.startswith("# Skills data"):
            mode = "skills"
            continue
        if stripped.startswith("# Perks data"):
            new_lines += build_skill_lines(skill_order, skill_ranks, skill_focuses, level, exp)
            mode = "perks"
            continue
        if stripped.startswith("# Crafting parts data"):
            if mode == "perks":
                new_lines += build_perk_lines(perks)
            mode = "copy"
            new_lines.append(line)
            continue

        if mode == "skills":
            if m := re.match(r"^level=(.*)", stripped):
                level = m.group(1)
            elif m := re.match(r"^exp=(.*)", stripped):
                exp = m.group(1)
            elif m := re.match(r"^(.*)Focus=(\d+)$", line):
                name = m.group(1).strip()
                skill_focuses[name] = m.group(2)
                if name not in skill_order:
                    skill_order.append(name)
            elif m := re.match(r"^(.*)=(\d+)$", line):
                name = m.group(1).strip()
                skill_ranks[name] = m.group(2)
                if name not in skill_order:
                    skill_order.append(name)
            continue

        if mode == "perks":
            if m := re.match(r"^(.*)\.(.*)=(\d+)$", line):
                perk, skill, val = m.group(1).strip(), m.group(2).strip(), m.group(3)
                perks.append((skill, perk, val))
            continue

        # copy mode with key tweaks
        if m := re.match(r"^(level|exp)=(.*)$", stripped):
            if m.group(1) == "level": level = m.group(2)
            else: exp = m.group(2)
            continue

        if m := re.match(r"^([^#=\s][^=]*)=(.*)$", line):
            key, val = m.group(1), m.group(2)
            if key == "companion": key = "isCompanion"
            elif key == "attributePoints": key = "attributePointsAvailable"
            elif key == "focusPoints": key = "focusPointsAvailable"
            val = norm_bool(val)
            line = f"{key}={val}"
        new_lines.append(line)

    # finalize tail sections if file ended before we flushed
    if mode == "skills":
        new_lines += build_skill_lines(skill_order, skill_ranks, skill_focuses, level, exp)
    if mode == "perks":
        new_lines += build_perk_lines(perks)

    return "\n".join(new_lines) + "\n"

def main():
    for path in Path(".").glob("*.txt"):
        if path.name == "Хальгард.txt":
            continue  # already new format
        new_path = path.with_suffix(".new.txt")
        new_path.write_text(convert(path), encoding="utf-8")
        print(f"converted {path.name} -> {new_path.name}")

if __name__ == "__main__":
    main()

