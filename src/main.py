def recommend_play(yards_to_go, yard_line):
    """
    Very simple beginner rules:
    - Short yardage near midfield → go for it
    - Long yardage deep in own territory → punt
    - Close enough for FG → kick
    """

    # Field goal range (rough)
    fg_range = yard_line >= 65

    if yards_to_go <= 2 and yard_line >= 45:
        return "GO FOR IT"
    elif fg_range:
        return "KICK FIELD GOAL"
    else:
        return "PUNT"


def main():
    yards_to_go = 2
    yard_line = 48

    decision = recommend_play(yards_to_go, yard_line)

    print("4th Down Decision")
    print("-----------------")
    print(f"Yards to go: {yards_to_go}")
    print(f"Yard line: {yard_line}")
    print(f"Recommendation: {decision}")


if __name__ == "__main__":
    main()

git add .
git commit -m "Add basic rule-based 4th down decision"
git push
