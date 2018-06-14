.. index:: {{ recording.title }}, {{ recording.artist }}
.. _hyperlink-name: "{{ recording.title }}" {{ recording.artist }}

"{{ recording.title }}" {{ recording.artist }}/{{ recording.year }}
===============================================


Recording Information
---------------------
.. list-table::
   :widths: 30 60
   :header-rows: 0

   * - Recording MusicBrainz ID (MBID)
     - `{{ annotation.mbid }}`_
   * - Time Signature
     - {{ annotation.metre }}
   * - Key
     - {{ ''.join(annotation.sandbox.key) }}
   * - Duration
     - {{ annotation.duration }} s
   * - Tuning
     - {{ annotation.tuning }} Hz
   * - Recording Dates
     - {{ recording.started }} - {{ recording.finished }}
   * - Composer(s)
     - {{ ', '.join(recording.composers) }}
.. _{{ annotation.mbid }}: https://musicbrainz.org/recording/{{ annotation.mbid }}

Line-up
-----------------------------------------------

.. list-table::
   :widths: 30 60
   :header-rows: 0
   {% for key, value in recording.lineup.items() %}
   * - {{key}}
     - {{', '.join(value)}} {% endfor %}

Symbolic Staistics From Annotation
-----------------------------------------------

.. list-table::
   :widths: 30 60
   :header-rows: 0

   * - Number of Chord Segments
     - {{ statistics.numberOfSegments }}
   * - Mean BPM
     - {{statistics.meanBPM}}
   * - :term:`Mean Harmonic Rhythm`
     - {{ statistics.meanHarmonicRhythm }}

.. list-table:: Chord Usage Summary
   :widths: 20 20 20 20 20
   :header-rows: 1

   * - Chord
     - Beats Number
     - Beats %
     - Duration (seconds)
     - Duration % {% for key, value in statistics.chordSummaryDict.items() %}
   * - {{key}}
     - {{value.beatsNumber}}
     - {{value.beatsPercent}}
     - {{value.durationSeconds}}
     - {{value.durationPercent}}{% endfor %}

Top Bigrams
-----------
(see :term:`Bigram` in glossary)

.. plot::

   import siteUtils
   siteUtils.showTop2GramsForFileList(['{{ jsonpathname }}'])

Top N-grams
-----------------------------------------------
(see :term:`N-gram` in glossary)

.. plot::

   import siteUtils
   siteUtils.showTopNGramsForFileList(['{{ jsonpathname }}'])

Chroma Statistics
-----------------------------------------------
:term:`Chord type chroma distribution ternary plot`

.. plot::

   import siteUtils
   siteUtils.show5HexagramsForFileList(['{{ jsonpathname }}'])

Source Annotation
-----------------------------------------------

:download:`{{ jsonname }} <{{ jsonpathname }}>`

.. literalinclude:: {{ jsonpathname }}
   :language: javascript

