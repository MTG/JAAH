function nmat = simpleSequence(tempo, chords)
nmat = zeros(0, 7);
onset = 0;
for c=chords
    nmat = appendChord(nmat, chord2midi(char(c)), onset, 1, 1, 60, onset * 60.0/tempo, 60.0/tempo);
    onset = onset + 1;
end
end


