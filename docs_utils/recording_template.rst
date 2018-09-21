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
     - {{ ''.join(annotation.key) }}
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
     - {{ statistics.number_of_segments }}
   * - Mean BPM
     - {{statistics.mean_bpm}}
   * - :term:`Mean Harmonic Rhythm`
     - {{ statistics.mean_harmonic_rhythm }}

.. list-table:: Chord Usage Summary
   :widths: 20 20 20 20 20
   :header-rows: 1

   * - Chord
     - Beats Number
     - Beats %
     - Duration (seconds)
     - Duration % {% for key, value in statistics.chord_summary_dict.items() %}
   * - {{key}}
     - {{value.beats_number}}
     - {{value.beats_percent}}
     - {{value.duration_seconds}}
     - {{value.duration_percent}}{% endfor %}

Top Bigrams
-----------
(see :term:`Bigram` in glossary)

.. plot::

   import site_utils
   site_utils.show_top_two_grams_for_file_list(['{{ jsonpathname }}'])

Top N-grams
-----------------------------------------------
(see :term:`N-gram` in glossary)

.. plot::

   import site_utils
   site_utils.show_top_n_grams_for_file_list(['{{ jsonpathname }}'])

Chroma Statistics
-----------------------------------------------
:term:`Chord type chroma distribution ternary plot`

.. plot::

   import site_utils
   site_utils.show_five_hexagrams_for_file_list(['{{ jsonpathname }}'])

Source Annotation
-----------------------------------------------

:download:`{{ jsonname }} <{{ jsonpathname }}>`

.. literalinclude:: {{ jsonpathname }}
   :language: javascript

