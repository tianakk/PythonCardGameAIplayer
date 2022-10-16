
# Rakesh Khanna ID:260944862
# Bassem Sandeela ID: 260975060
# Tiana Koundakjian ID:260949364
# Xiao Fan Guan ID:260983910
# Alexis Viau-Cardinal ID: 260988139

import arrangement
import random
import doctest
from card import *

def draw(hand, top_discard, last_turn, picked_up_discard_cards, player_position, wildcard_rank, num_turns_this_round):
    """ (list,int,bool,list,int,int)-> str

    This function returns either the string stock or discard.

    >>> draw([5,6,7], 8, True, [[12,14,45],[43, 12, 33],[51, 22]], 0, 3, 4)
    'discard'

    >>> draw([3, 51, 50, 52, 3, 1, 8, 49, 52], None, True, [[9,43,49],[5,48],[32,35]], 1, 7, 9)
    'stock'

    >>> draw([43, 50, 10, 42, 23, 12, 33, 14, 43, 23], 4, False, [[40, 39, 33], [2, 25], [12, 33]], 2, 2, 5)
    'discard'

    """
    # checks if there's a card on the discard pile
    if top_discard == None:
        # if there are not any card, we are forced to choose 'stock'
        return 'stock'
    elif get_rank(top_discard) == wildcard_rank: # if the top card is a wildcard, take it since it is versatile
        return 'discard'

    # grabs the possible sequences and group in the current
    hand_grouped = arrangement.get_arrangement(tuple(hand), wildcard_rank)

    # Evaluates how useful is the card on the discard pile
    hand2 = hand + [top_discard]
    hand2_grouped = arrangement.get_arrangement(tuple(hand2), wildcard_rank)
    if len(hand2_grouped) > len(hand_grouped): # if there are more combinations in the new hand, than choose the discard
        return 'discard'

    # Returns 'stock' most of the time, but also returns 'discard' sometimes to confuse other player and maybe obtain new sequences
    # Takes into account the rank of the card being picked up so it does not disadvantages the player too much
    return 'stock' if random.random() < (get_rank(top_discard)+2)/ACE else 'discard'

def discard(hand, last_turn, picked_up_discard_cards, player_position, wildcard_rank, num_turns_this_round):
    """" (list,int,bool,list,int,int)-> str
    This function returns a card from the hand to discard.

    >>> random.seed(1759)
    >>> card = discard([21, 47, 20, 17, 46, 1, 50, 29, 2, 14, 30], False, [[12, 44, 33, 41], [43, 3, 7, 47], [17, 36]], 0, 7, 5)
    >>> card
    1

    >>> card = discard([42, 15, 7, 25, 9, 45, 48, 37, 40], False, [[29, 10, 49], [24, 8], [1, 21, 28, 40]], 1, 11, 5)
    >>> card
    9

    >>> card = discard([51, 33, 2, 26, 28, 37, 42, 45, 19, 27, 43], True, [[7, 44, 19], [20, 13, 33, 13], [5, 48, 36, 46]], 0, 0, 3)
    >>> card
    42

    """
    # Creates a few basic arrays:
    # 'combinations' is a 2D array of the current best hand
    combinations = arrangement.get_arrangement(tuple(hand), wildcard_rank)
    # 'locked_cards' holds each card in 'combinations' in a 1D array
    locked_cards = arrangement_to_hand(combinations)
    # 'remaining' holds the card in the hand that are not used in the best combination
    remainders = remaining(hand, locked_cards)

    # If it is the last turn, then get rid of the highest ranked useless card
    if last_turn:
        return max_penalty(remainders if len(remainders) > 0 else hand)

    # Computes the possible combinations easily obtainable using the '_close_combination' function
    possibilities = _close_combination(hand, wildcard_rank, combinations, locked_cards, remainders)

    # List of all the cards in hand required by the possibilities, contians redundancy
    uses = []
    for possibility in possibilities:
        if possibility[0] in ['group', 'sequence']:
            uses += possibility[2]

    # Cleans up uses by creating a dictionnary holding the card number as an index and the count of how many times that card appeared in 'uses' as a value
    uses_count = {}
    for card in list(dict.fromkeys(uses)):
        uses_count[card] = uses.count(card)


    # Extracts some cards that are judged less worthy than the others
    min_uses = []
    max_val = 10000
    for card, count in uses_count.items():
        if count < max_val-2:
            max_val = count+2
            min_uses = [card]
        elif count <= max_val:
            min_uses.append(card)

    # Grabs the array holding the list of the cards picked up by the player next to this bot
    next_user = picked_up_discard_cards[(player_position+1)%len(picked_up_discard_cards)]
    to_return = [] # 'to_return' are cards deemed safe to discarded
    maybe = [] # 'maybe' are cards that hold a certain risk to be discarded but may not advantage the other player

    # Iterates through the cards deemed useless
    for card in min_uses:
        # get the suit and rank of the card
        suit = get_suit(card)
        rank = get_rank(card)
        if card in next_user: # if the user once picked the exact card that we are about to throw
            # we put this card in maybe because if the other user was doing a sequence and not a group, this card does not help them at all
            maybe.append(card)
            continue
        if (rank + 1) in RANKS and get_card(suit, rank+1) in next_user:
            # if the user picked up a card of the same suit, one rank higher, disregard it since they can make a sequence
            continue
        if (rank - 1) in RANKS and get_card(suit, rank-1) in next_user:
            # if the user picked up a card of the same suit, one rank below, disregard it since they can make a sequence
            continue
        for suit in SUITS: # if the user picked up a card of the same rank but different suit, do not discard since we allow them to make a group
            if get_card(suit, get_rank(card)) in next_user:
                continue
        to_return.append(card) # if non of these cases apply, this card is deemed safe therefore added to the 'to_return' list

    if len(to_return) > 0: # if there are any safe card, return the most penalizing one
        return max_penalty(to_return)
    elif len(maybe) > 0: # if there are any semi-safe card, return the most penalizing one
        return max_penalty(maybe)
    elif len(remainders) > 0: # if all cards are likely to help the next player, return the most penalizing card not used
        return max_penalty(remainders)

    return max_penalty(hand) # if we have one extra card, meaning that we were trying to do a group with more cards than we are allow, returns the most penalizing card again


def _close_combination(hand, wildcard, combinations, locked_cards, remaining):
    # wildcard_count = len([0 for card in hand if get_rank(card) == wildcard])
    # wildcard_used = len([0 for card in locked_cards if get_rank(card) == wildcard])

    # Sorts the hand by suit and by rank using 'sort_by' function
    all_sorted_suit = {}
    all_sorted_rank = {}
    sort_by(hand, all_sorted_suit, all_sorted_rank)

    # remaining_wildcard = wildcard_count - wildcard_used

    # Sorts the cards not used by suit and by rank using 'sort_by' function
    remaining_sorted_suit = {}
    remaining_sorted_rank = {}
    sort_by(remaining, remaining_sorted_suit, remaining_sorted_rank)


    # Start listing possibilities
    # Elements in possibilities are of the following form (TYPE:string, CARD_REQUIRED:int, HAND_CARD_AFFECTED:int[])
    possibilities = []

    # Checks for possible groups in the available cards
    for rank, hand_list in remaining_sorted_rank.items(): # iterates through each rank
        if len(hand_list) == 2: # If a rank has two cards available
            for suit in SUITS: # Adds all other cards to the 'possibilities' watch list
                card = get_card(suit, rank)
                for i in range(2-hand.count(card)):
                    possibilities.append(('group', card, [get_card(hand_list[0], rank),get_card(hand_list[1], rank)]))



    # Checks for possible sequences to create
    for suit, suit_list in all_sorted_suit.items(): # iterates through each suit

        # Create strings that will represent the hand
        # Two because we may have more than one of the same card in the same suit since we are working with two decks
        card_present_1 = ''
        card_present_2 = ''

        # Converts the available hand into a string 'card_present_1'
        # Duplicate cards are sent to 'card_present_2'
        # '0' means that the card is not in the hand
        for rank in RANKS:
            card_present_1 += rank_to_letter(rank) if remaining.count(rank) >= 1 else '0'
            card_present_2 += rank_to_letter(rank) if remaining.count(rank) >= 2 else '0'

        # Splits the cards in groups accoring to the
        card_split_1 = card_present_1.split('0')
        card_split_2 = card_present_2.split('0')

        # Iterates through each island of cards
        for i, sub in enumerate(card_split_1):
            if len(sub) == 1: # if the island is of lenght one
                sub_to_int = [letter_to_rank(sub)]
                if i+1 < len(card_present_1): # If the next island is spaced within 1 card difference, add it to the possibilities
                    if letter_to_rank(card_present_1[i+1][0])-letter_to_rank(sub[0]) <= 2:
                        possibilities.append(('sequence', letter_to_rank(sub[-1])+1, sub_to_int))
                if i-1 >= 0: # If the previous island is spaced within 1 card difference, add it to the possibilities
                    if letter_to_rank(sub[0])-letter_to_rank(card_present_1[i-1][-1]) <= 2:
                        possibilities.append(('sequence', letter_to_rank(sub[0])-1, sub_to_int))
            elif len(sub) == 2: # If the island is of lenght 2
                sub_to_int = [letter_to_rank(sub[0]), letter_to_rank(sub[1])]

                # Adds the previous and the next card to the possibilities if possible
                if letter_to_rank(sub[1]) + 1 < len(card_present_1):
                    possibilities.append(('sequence', letter_to_rank(sub[1])+1, sub_to_int))
                if letter_to_rank(sub[0]) - 1 >= 0:
                    possibilities.append(('sequence', letter_to_rank(sub[0])-1, sub_to_int))

    # Checks for extensions of current sequences and groups
    for groupings in combinations: # Iterates through the sequences
        if arrangement.is_valid_sequence(groupings, wildcard):
            # Adds the card above and below to the possibilites
            if get_rank(groupings[0]) - 1 >= 0:
                possibilities.append(('sequence-extension', get_card(get_suit(groupings[0]), get_rank(groupings[0]) - 1)))
            if get_rank(groupings[0]) + 1 < len(RANKS):
                possibilities.append(('sequence-extension', get_card(get_suit(groupings[0]), get_rank(groupings[0]) + 1)))
        else:
            if len(groupings) < 8: # If we do not have all the cards of the 'groupings'
                rank = get_rank(groupings[0])
                for suit in SUITS: # Iterates through each suit
                    card = get_card(suit, rank)
                    for i in range(2-groupings.count(card)): # Adds card remaining of the same rank
                        possibilities.append(('group-extension', card))
    return possibilities

def max_penalty(card_arr):
    ''' (int[]) -> int
    Computes the maximum penalty obtainable with by the passed array

    >>> max_penalty([3, 51, 50, 52, 3, 1, 8, 49, 52])
    8

    >>> max_penalty([43, 50, 10, 42, 23, 12, 33, 14, 43, 23])
    43

    >>> max_penalty([12, 44, 33, 41])
    44
    '''
    rank_array = []
    for card in card_arr:
        rank = get_rank(card)
        rank_array += [rank + 2] if rank != ACE else [1]
    return card_arr[rank_array.index(max(rank_array))]

def rank_to_letter(a):
    ''' (int) -> char
    Returns a letter interpretation of a rank

    >>> rank_to_letter(0)
    'a'

    >>> rank_to_letter(1)
    'b'

    >>> rank_to_letter(10)
    'k'
    '''
    return str(chr(a+97))

def letter_to_rank(a):
    ''' (char) -> int
    Returns a rank interpretation of a letter

    >>> letter_to_rank('a')
    0

    >>> letter_to_rank('b')
    1

    >>> letter_to_rank('k')
    10
    '''
    return ord(a)-97

def arrangement_to_hand(arrangement):
	''' (int[][]) -> int[]
	Takes in an arrangement and returns a one-dimension array
	If an element appears in more than one subgroup, it will be repeated

	>>> arrangement_to_hand([[12, 44, 33, 41], [43, 3, 7, 47], [17, 36]])
	[12, 44, 33, 41, 43, 3, 7, 47, 17, 36]

	>>> arrangement_to_hand([[9,43,49],[5,48],[32,35]])
	[9, 43, 49, 5, 48, 32, 35]

	>>> arrangement_to_hand([[40, 39, 33], [2, 25], [12, 33]])
	[40, 39, 33, 2, 25, 12, 33]
	'''
	return_arr = []
	# iterates through each card
	for group in arrangement:
		for card in group:
			return_arr.append(card) # adds the card to our return array
	return return_arr

def remaining(hand, locked_cards, REMAINING = None):
	''' (int[], int[], int[]) -> int[]
	Removes 'locked_cards' from 'hand' yields the result if 'REMAINING' is None, otherwise appends to REMAINING

	>>> remaining([12, 44, 33, 41, 43, 3, 7, 47, 17, 36], [12, 43, 36])
	[44, 33, 41, 3, 7, 47, 17]

	>>> arr = []
	>>> remaining([12, 44, 33, 41, 43, 3, 7, 47, 17, 36], [12, 43, 36], arr)
	>>> arr
	[44, 33, 41, 3, 7, 47, 17]

	>>> remaining([9, 23, 34, 5, 5, 32, 35, 32], [5, 32])
	[9, 23, 34, 5, 32, 35]
	'''
	remainders = []
	for card in list(dict.fromkeys(hand)): # iterates once through each different card
	    remainders += [card] * (hand.count(card) - locked_cards.count(card)) # adds
	if REMAINING == None:
	    return remainders
	REMAINING += remainders

def sort_by(cards, suit_d, rank_d):
    ''' (int[], {int:[]}, {int:[]})
    Sorts the cards by rank and suit in dictionnaries
    '''
    for card in cards: # Iterates through each card
        # Gets the rank and suit
        suit = get_suit(card)
        rank = get_rank(card)

        # Defines the rank or suit if not defined in dictionnaries
        if suit_d.get(suit) == None:
            suit_d[suit] = []
        if rank_d.get(rank) == None:
            rank_d[rank] = []

        # Append the card to the proper location
        suit_d[suit].append(rank)
        rank_d[rank].append(suit)

    # For convininence purposes, sorts the ranks of the card in each suit
    for suit, hand_list in suit_d.items():
        hand_list.sort()


if __name__ == '__main__':
    doctest.testmod()
# Rakesh Khanna ID:260944862 
# Bassem Sandeela ID: 260975060
# Tiana Koun