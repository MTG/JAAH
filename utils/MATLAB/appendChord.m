function nmat = appendChord(nmat, midiNotes, beatsOnset, beatsDuration, chanel, velocity, secOnset, secDuration)
for n=midiNotes
    nmat(end+1,:) = [beatsOnset, beatsDuration, chanel, n, velocity, secOnset, secDuration];
end    
end