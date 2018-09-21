function sonify(annotationFile, inAudioFile, outAudioFile, chordsBalanceCorrection, dd5)
%SONIFY sonify chord sequence and mix it down with the original audio.
% annotationFile - chord annotations in "lab" format
% inAudioFile - audio file to mix with sonification
% outAudioFile - name of resulting file
% chordsBalanceCorrection - default is 0.075.
%                           Greater numbers attenuates chords sound.
%                           Lower numbers make it louder.
%

if nargin<5
   dd5 = 0;
   if nargin<4
       chordsBalanceCorrection = 0.075;
   end
end

inAudioFile
[y,Fs] = audioread(inAudioFile);

s = readtable(annotationFile, 'FileType', 'text');
nmat = zeros(0, 7);
segments = zeros(0,2);
for i = 1:size(s,1)
   onset = s.Var1(i);
   duration = s.Var2(i) - onset;
   chord = char(s.Var3(i));
   if (chord ~= 'N')
       nmat = appendChord(nmat, chord2midi(char(chord), dd5), onset, duration, 1, 60, onset, duration);
       segments(end+1, :) = [round(s.Var1(i)*Fs) + 1 round(s.Var2(i)*Fs)];       
   end
end

chordsAudio=mynmat2snd(nmat,'shepard',Fs);

% assuming files are in stereo.
if length(y) < length(chordsAudio)
    chordsAudio=chordsAudio(1:length(y));
    chordsAudio=[chordsAudio;chordsAudio]';
elseif length(y) > length(chordsAudio)
    y=y(1:length(chordsAudio), :);
    chordsAudio=[chordsAudio;chordsAudio]';   
end        

% equalization
mc = [];
mo = [];
for i=1:size(segments, 1)
    i
    s=segments(i,1):segments(i,2);
    r = Loudness_TimeVaryingSound_Zwicker(y(s,1), Fs);
    meanOrig = mean(r.InstantaneousLoudness);
    r = Loudness_TimeVaryingSound_Zwicker(chordsAudio(s,1), Fs);
    meanChords = mean(r.InstantaneousLoudness);
    
    mo(end+1)=meanOrig;
    mc(end+1)=meanChords;
end
%plot(1:size(segments, 1), mo, 1:size(segments, 1), mc);

delta = exp((mo - 10 - mc) * chordsBalanceCorrection);

newChordsAudio=chordsAudio;
for i=1:size(segments, 1)
    s=segments(i,1):segments(i,2);
    newChordsAudio(s,:)= delta(i) * chordsAudio(s,:);
end

%clear sound
%sound((newChordsAudio + y)/2,Fs);
audiowrite(outAudioFile, (newChordsAudio + y)/2, Fs);
%audiowrite(outAudioFile, newChordsAudio, Fs);   

end


