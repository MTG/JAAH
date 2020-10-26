"""
    This script is to change the keys in the classical jazz format (version 1.0) to MIREX format

    In classical jazz format, the keys are:

    39 giant_steps It doesnt have a key defined.
    0 airegin Ab
    1 all_alone C
    2 bags_groove F
    3 big_butter_and_eggman G
    4 bikini Bb:min
    5 black_and_tan_fantasy Bb
    6 black_bottom_stomp Bb
    7 black_water_blues A
    8 blue_7 Bb
    9 blue_horizon Eb
    10 blue_serge C:min
    11 blues_for_alice.mp3 F
    12 blues_in_the_closet Bb
    13 body_and_soul(goodman) Db
    14 body_and_soul(hawkins) Db
    15 boplicity F
    16 breakfast_feud Bb
    17 concerto_for_cootie F
    18 cotton_tail Bb
    19 cotton_tail_fitzgerald Bb
    20 crazeology Bb
    21 daahoud B
    22 dead_man_blues Bb
    23 dexter_rides_again F
    24 diminuendo_and_crescendo_in_blue Eb
    25 dinah G
    26 dinah_fats_waller Ab
    27 dinah_red_nichols Ab
    28 dippermouth_blues C
    29 django F:min
    30 doggin_around Bb
    31 east_st_louis C:min
    32 embraceable_you F
    33 everybody_loves_my_baby G:min
    34 evidence Eb
    35 for_dancers_only Eb
    36 four_brothers Ab
    37 four_or_five_times Eb
    38 from_monday_on Bb
    40 girl_from_ipanema Db
    41 grandpas_spells C
    42 haig_and_haig Bb
    43 handful_of_riffs D
    44 harlem_congo Eb
    45 he_s_funny_that_way Bb
    46 honeysuckle_rose Db
    47 honky_tonk_train G
    48 hotter_than_that Eb
    49 i_cant_believe_you_are_in_love_with_me C#
    50 i_cant_get_started C
    51 i_found_a_new_baby F
    52 i_got_rhythm Bb
    53 i_gotta_right_to_sing_the_blues G
    54 in_a_mellotone Db
    55 in_gloryland Ab
    56 indiana F
    57 isfahan Db
    58 king_porter_stomp Ab
    59 ko-ko(ellington) Eb:min
    60 lady_bird C
    61 lester_leaps_in Bb
    62 livery_stable_blues Eb
    63 lost_your_head_blues Eb
    64 manteca Bb
    65 maple_leaf_rag(bechet) Eb
    66 maple_leaf_rag(braxton) Ab
    67 maple_leaf_rag(hyman) Ab
    68 mean_to_me C
    69 minor_swing A:min
    70 misterioso Bb
    71 moanin F:min
    72 moten_swing Eb
    73 my_favorite_things E
    74 new_east_st_louis F:min
    75 night_in_tunisia D:min
    76 oh_lady_be_good G
    77 one_by_one G:min
    78 one_oclock_jump F
    79 organ_grinders_swing Eb
    80 parkers_mood Bb
    81 pentup_house G
    82 potato_head_blues F
    83 riverboat_shuffle Ab
    84 rockin_chair Eb
    85 september_in_the_rain Eb
    86 shaw_nuff Bb
    87 singin_the_blues Eb
    88 st_louis_blues D
    89 st_thomas C
    90 stompin_at_the_savoy Db
    91 struttin_with_some_barbecue Ab
    92 subconscious_lee C
    93 summertime Bb:min
    94 sweethearts_on_parade F
    95 swing_that_music C
    96 thats_a_serious_thing Bb
    97 the_golden_bullet F
    98 the_man_i_love Eb
    99 the_preacher F
    100 the_stampede Ab
    101 these_foolish_things Ab
    102 tricroism Db
    103 walkin_shoes G
    104 watermelon_man F
    105 weather_bird Ab
    106 west_coast_blues Bb
    107 west_end_blues Eb
    108 when_lights_are_low Ab
    109 work_song F:min
    110 wrap_your_troubles_in_dreams A
    111 wrappin_it_up Db
    112 you_d_be_so_nice_to_come_home_to Db

    New keys:
    0 airegin Ab major
    1 all_alone C major
    2 bags_groove F major
    3 big_butter_and_eggman G major
    4 bikini Bb minor
    5 black_and_tan_fantasy Bb major
    6 black_bottom_stomp Bb major
    7 black_water_blues A major
    8 blue_7 Bb major
    9 blue_horizon Eb major
    10 blue_serge C minor
    11 blues_for_alice F major
    12 blues_in_the_closet Bb major
    13 body_and_soul(goodman) Db major
    14 body_and_soul(hawkins) Db major
    15 boplicity F major
    16 breakfast_feud Bb major
    17 concerto_for_cootie F major
    18 cotton_tail Bb major
    19 cotton_tail_fitzgerald Bb major
    20 crazeology Bb major
    21 daahoud B major
    22 dead_man_blues Bb major
    23 dexter_rides_again F major
    24 diminuendo_and_crescendo_in_blue Eb major
    25 dinah G major
    26 dinah_fats_waller Ab major
    27 dinah_red_nichols Ab major
    28 dippermouth_blues C major
    29 django F minor
    30 doggin_around Bb major
    31 east_st_louis C minor
    32 embraceable_you F major
    33 everybody_loves_my_baby G minor
    34 evidence Eb major
    35 for_dancers_only Eb major
    36 four_brothers Ab major
    37 four_or_five_times Eb major
    38 from_monday_on Bb major
    39 giant_steps X
    40 girl_from_ipanema Db major
    41 grandpas_spells C major
    42 haig_and_haig Bb major
    43 handful_of_riffs D major
    44 harlem_congo Eb major
    45 he_s_funny_that_way Bb major
    46 honeysuckle_rose Db major
    47 honky_tonk_train G major
    48 hotter_than_that Eb major
    49 i_cant_believe_you_are_in_love_with_me C# major
    50 i_cant_get_started C major
    51 i_found_a_new_baby F major
    52 i_got_rhythm Bb major
    53 i_gotta_right_to_sing_the_blues G major
    54 in_a_mellotone Db major
    55 in_gloryland Ab major
    56 indiana F major
    57 isfahan Db major
    58 king_porter_stomp Ab major
    59 ko-ko(ellington) Eb minor
    60 lady_bird C major
    61 lester_leaps_in Bb major
    62 livery_stable_blues Eb major
    63 lost_your_head_blues Eb major
    64 manteca Bb major
    65 maple_leaf_rag(bechet) Eb major
    66 maple_leaf_rag(braxton) Ab major
    67 maple_leaf_rag(hyman) Ab major
    68 mean_to_me C major
    69 minor_swing A minor
    70 misterioso Bb major
    71 moanin F minor
    72 moten_swing Eb major
    73 my_favorite_things E major
    74 new_east_st_louis F minor
    75 night_in_tunisia D minor
    76 oh_lady_be_good G major
    77 one_by_one G minor
    78 one_oclock_jump F major
    79 organ_grinders_swing Eb major
    80 parkers_mood Bb major
    81 pentup_house G major
    82 potato_head_blues F major
    83 riverboat_shuffle Ab major
    84 rockin_chair Eb major
    85 september_in_the_rain Eb major
    86 shaw_nuff Bb major
    87 singin_the_blues Eb major
    88 st_louis_blues D major
    89 st_thomas C major
    90 stompin_at_the_savoy Db major
    91 struttin_with_some_barbecue Ab major
    92 subconscious_lee C major
    93 summertime Bb minor
    94 sweethearts_on_parade F major
    95 swing_that_music C major
    96 thats_a_serious_thing Bb major
    97 the_golden_bullet F major
    98 the_man_i_love Eb major
    99 the_preacher F major
    100 the_stampede Ab major
    101 these_foolish_things Ab major
    102 tricroism Db major
    103 walkin_shoes G major
    104 watermelon_man F major
    105 weather_bird Ab major
    106 west_coast_blues Bb major
    107 west_end_blues Eb major
    108 when_lights_are_low Ab major
    109 work_song F minor
    110 wrap_your_troubles_in_dreams A major
    111 wrappin_it_up Db major
    112 you_d_be_so_nice_to_come_home_to Db major
"""
import os
import re


def to_mirex(ann):
    # if key is not defined
    if ann is None:
        return 'X'
    # if key is minor
    if ann[-4:] == ":min":
        return ann[:-4] + " minor"
    else:
        return ann + " major"


def reformat_file(path):
    with open(path, 'r+') as f:
        content = f.readlines()
        f.seek(0)
        #For major:
        content = re.sub('("key": ".[b#]?)"', r'\1 major"', content, flags=re.MULTILINE)
        #For minor
        content = re.sub('("key": ".[b#]?):min"', r'\1 minor"', content, flags=re.MULTILINE)
        f.write(content)
        f.truncate()


def reformat_keys():
    directory = "../annotations/"
    for i, ann_file in enumerate(sorted(os.listdir(directory))):
        print(i, ann_file.replace(".json", ''), end=' ')
        reformat_file(directory + ann_file)


if __name__ == '__main__':
    reformat_keys()
