from hypothesis import given
import hypothesis.strategies as st

import cards

@given(no = st.integers(min_value=0, max_value=cards.CARDS))
def test_get_name_and_image(no):
    cards.get_name(no)
    cards.get_image(cards.im, no)
