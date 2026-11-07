"""History: loop detection fails the run once one long line appears four times."""

import homebench


LINE = "We'll also need to handle the spawn interval reduction."
FILLER = "Distinct planning sentence number {} about the car."


def _answer_with_repeated_line(repeats):
    blocks = []
    for index in range(repeats):
        blocks.append(LINE)
        blocks.append(FILLER.format(index))
    return "\n\n".join(blocks)


def test_four_identical_long_lines_trigger_the_loop_detector():
    assert homebench._detect_repetition_loop(_answer_with_repeated_line(4))


def test_three_identical_long_lines_do_not_trigger_the_loop_detector():
    assert not homebench._detect_repetition_loop(_answer_with_repeated_line(3))


def test_short_repeated_lines_do_not_trigger_the_loop_detector():
    assert not homebench._detect_repetition_loop("\n".join(["return;"] * 12))


def test_repeated_code_lines_do_not_trigger_the_loop_detector():
    code = "gain.gain.setValueAtTime(0.3, now);"
    assert not homebench._detect_repetition_loop("\n".join([code] * 4))
