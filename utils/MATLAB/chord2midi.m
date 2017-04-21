function midiNotes = chord2midi(s, dd5)
  persistent shortcuts;
  persistent notes;
  persistent degrees;
  persistent alterations;
  if (isempty(shortcuts))
      shortcuts=containers.Map;
      shortcuts('maj')='(3,5)';
      shortcuts('min')='(b3,5)';
      shortcuts('dim')='(b3,b5)';
      shortcuts('aug')='(3,#5)';
      shortcuts('maj7')='(3,5,7)';
      shortcuts('min7')='(b3,5,b7)';
      shortcuts('7')='(3,5,b7)';
      shortcuts('dim7')='(b3,b5,bb7)';
      shortcuts('hdim7')='(b3,b5,b7)';
      shortcuts('minmaj7')='(b3,5,7)';
      shortcuts('maj6')='(3,5,6)';
      shortcuts('min6')='(b3,5,6)';
      shortcuts('9')='(3,5,b7,9)';
      shortcuts('maj9')='(3,5,7,9)';
      shortcuts('min9')='(b3,5,b7,9)';
      shortcuts('sus4')='(4,5)';
      
      notes=containers.Map;
      notes('C')=0;
      notes('D')=2;
      notes('E')=4;
      notes('F')=5;
      notes('G')=7;
      notes('A')=9;
      notes('B')=11;
      
      degrees=containers.Map;
      degrees('1')=0;
      degrees('2')=2;
      degrees('3')=4;
      degrees('4')=5;
      degrees('5')=7;
      degrees('6')=9;
      degrees('7')=11;
      degrees('9')=14;
      degrees('11')=17;
      degrees('13')=21;

      alterations=containers.Map;
      alterations('b')=-1;
      alterations('#')=1;
  end
  if nargin<2
    dd5 = 0
  end
  c = strsplit(s, ':');
  rc = strsplit(char(c(1)), '/');
  root = char(rc(1));
  if (size(c,2) == 1)
      c = 'maj';
  else
      c = c(2);
  end
  c = strsplit(char(c), '/');
  pattern = char(c(1));
  if (isKey(shortcuts, pattern))
      if (strcmp(pattern, '7') &&  dd5)
          pattern = '(3,b7)';
      else
          pattern = shortcuts(pattern);
      end    
  end
  rootMidi = notes(root(1));
  for c = root(2:end)
      rootMidi = rootMidi + alterations(c);
  end
  pattern=regexprep(pattern,'[()]','');
  ds = strsplit(pattern, ',');
  midiNotes = zeros(1, size(ds, 2) + 1);
  midiNotes(1) = rootMidi;
  i = 2;
  for d = ds
      d = strtrim(d);
      newMidi = 0;
      for c = char(d(1:end))
          if (isKey(alterations, c))
              newMidi = newMidi + alterations(c);
          else
              newMidi = newMidi + degrees(c) + rootMidi;
              break
          end
      end
      midiNotes(i) = newMidi; 
      i = i + 1;
  end
  midiNotes = mod(midiNotes, 12) + 60;
  %midiNotes = midiNotes + 60;
end


