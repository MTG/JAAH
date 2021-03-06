.. Jazz Audio-Aligned Harmony (JAAH) Dataset documentation master file, created by
   sphinx-quickstart on Thu Jan 25 18:28:21 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Jazz Audio-Aligned Harmony (JAAH) Dataset's documentation!
===============================================

* `Dataset statistics`_
* `Contents`_
* `Glossary`_
* `References`_
* :ref:`genindex`
* :ref:`search`

Dataset statistics
------------------

.. list-table::
   :widths: 30 60
   :header-rows: 0

   * - Contains
     - {{ overview.size }} tracks
   * - Time period
     - {{ overview.first_year }} - {{ overview.last_year }}
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

Histogram by year
-----------------

.. plot::

   import site_utils
   site_utils.show_year_histogram_for_file_list(site_utils.file_list('{{ anno_directory }}'))

Top Bigrams
-----------------------------------------------

(see :term:`Bigram` in glossary)

.. plot::

   import site_utils
   site_utils.show_top_two_grams_for_file_list(site_utils.file_list('{{ anno_directory }}'))

Top N-grams
-----------------------------------------------

(see :term:`N-gram` in glossary)

.. plot::

   import site_utils
   site_utils.show_top_n_grams_for_file_list(site_utils.file_list('{{ anno_directory }}'))

Chroma Statistics
-----------------------------------------------
:term:`Chord type chroma distribution ternary plot`

.. plot::

   import site_utils
   site_utils.show_five_hexagrams_for_file_list(site_utils.file_list('{{ anno_directory }}'))

Contents
--------

.. toctree::
   :maxdepth: 1
   :glob:

   data/*

Glossary
--------

.. glossary::

   Bigram
      Bigram represents chords transition event.
      "Absolute" chord pitches are omitted, bigram is denoted by:

       - first chord quality (i.e. Maj, Min, Dom, HDim7, Dim)
       - interval between first and second chord roots encoded by:

          - Letter: **P**\ erfect, **M**\ ajor  or
            **m**\ inor
          - number (2 for second, 3 for third, etc)

       - second chord quality

      The approach is taken from :cite:`Broze2013`.

   N-gram
      Represent sequence of chord transition events.
      "Absolute" chord pitches are omitted, only chord qualities
      and inter-root intervals are considered (see :term:`Bigram`).

   Chord type chroma distribution ternary plot
      Lead sheet chord chart is the backbone of performance in
      many jazz styles. But each performance and style has it's own "sonic aura"
      determined by how conceived chords are realized by musicians.
      The main idea of these plots is to provide visual profiles
      for each of main chord types used in jazz (major, minor, dominant seventh,
      halfdiminished seventh and diminished) for the whole dataset and for each track.
      Chroma distribution plots show:

      - What degrees (relative to a chord's root) are actually presented,
        and quantitative measurement of their presence.
      - Joint distribution of the degrees (it shows e.g. how often certain degrees are
        played together or are they used independently)
      - Dispersion of degree usage

      How are they produced?

      1. **NNLS Chroma** features (http://www.isophonics.net/nnls-chroma , :cite:`Mauch2010`)
         are extracted for each frame of audio recordings.
         Each chroma is a 12-dimensional vector, with components representing
         12 semitone pitch classes.
      4. Pitch-class based chroma converted to **degree-based chroma**.
         I.e. chroma vectors corresponding to each particular chord
         are transposed to the common root, so the new vector's first component
         represents intensity of chord root pitch, the following -
         intensity of minor second, etc.
      2. For each beat, **"beat predominant chroma"** is calculated.
         This is a single 12d vector which represents predominant chroma
         around this beat. To estimate it, we convolve per-frame chroma vectors with
         Hanning window (https://en.wikipedia.org/wiki/Hann_function)
         and then use vectors corresponding to beat frames.
         Thus, maximum weights are given to frames, close to the beat and
         weights are decreased as frames are moving away from the beat.
      5. We rather interested in proportion of chroma components in
         a certain sound segment, but not in it's absolute values,
         so we **normalize** them with :math:`l1` norm. So they are sum up to one
         (and they are non-negative by definition).
      6. Normalized chroma vectors don't fill the whole 12D space.
         They are distributed on standard 11-simplex
         (https://en.wikipedia.org/wiki/Simplex):
         :math:`\{x\in \mathbb {R} ^{12}:x_{0}+\dots +x_{11}=1,x_{i}\geq 0,i=0,\dots ,11\}`.
         To visualize it's distribution we borrow techniques from
         Compositional Data Analysis (e.g. :cite:`VandenBoogaart2013`).
         Such techniques are used when proportions of parts is
         explored (e.g. chemical composition or budget composition).
         Our 11-d simplex has 12 vertices corresponding to 12 semitones addressed as
         chord degrees. It's confined by 220 triangle faces
         (each face corresponds to unique triple combination of the degrees, e.g. I-III-V).
         To see what's inside, we produce two dimensional projections of the simplex content
         to it's faces, representing density with color. For each triple
         we marginalize out chroma components which are not inculded in the triple
         and obtain distribution of 3 chord degrees which is defined on a triangle.
         Resulted figure is called **Ternary plot** (https://en.wikipedia.org/wiki/Ternary_plot).
         Out of 220 triangles, we show only six, related to the most "significant" chord degrees.
         ("Significance" here means that chroma components for these degrees have highest average values
         throughout the whole dataset), triangles are arranged into hexagons adjoined by identical
         edges for presentation simplicity.

   Mean harmonic rhythm
      Rate (in chords per beat) at which chords are changed.
      See e.g.: https://en.wikipedia.org/wiki/Harmonic_rhythm

References
----------

.. bibliography:: references.bib
