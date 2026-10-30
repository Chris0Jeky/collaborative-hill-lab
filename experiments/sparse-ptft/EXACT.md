# Sparse pTFT — exact labeled-state readout

Offline analytical extension; no stochastic episodes or measured discrepancies.

Sixteen declared cells, eight observed rounds t=0,...,7, zero exploration.
All pTFT actors start C; fixed AllD actors stay D. Every entry is an exact fraction.
Cooperation weights vertices equally, including AllD, and includes the initial round.

| Condition | E[mean cooperation] | Var(mean cooperation) | P(first all-D <= 7) |
|---|---:|---:|---:|
| complete3-m2-include_self | 6305/26244 | 12504421/688747536 | 4363129/4782969 |
| complete3-m2-exclude_self | 85/512 | 30847/4718592 | 16129/16384 |
| complete5-m4-include_self | 325089/781250 | 16042296217/610351562500 | 22142339110513616401/37252902984619140625 |
| complete5-m4-exclude_self | 11795/32768 | 454545627/21474836480 | 50783858880981505/72057594037927936 |
| complete5-m3-include_self | 72012/390625 | 18184744287/2441406250000 | 448432091581328/476837158203125 |
| complete5-m3-exclude_self | 153/1024 | 216773709/53687091200 | 8426323333/8589934592 |
| cycle4-m3-include_self | 3383/8748 | 15600077/612220032 | 3039680/4782969 |
| cycle4-m3-exclude_self | 75/256 | 951/65536 | 203/256 |
| star4-hub-alld-include_self | 765/4096 | 92541/16777216 | 2048383/2097152 |
| star4-hub-alld-exclude_self | 3/32 | 0 | 1 |
| star4-leaf-alld-include_self | 277095/524288 | 9038584463/274877906944 | 12730573/33554432 |
| star4-leaf-alld-exclude_self | 1105/2592 | 47663/1679616 | 1235/2187 |
| cycle4-all-ptft-include_self | 1 | 0 | 0 |
| cycle4-all-ptft-exclude_self | 1 | 0 | 0 |
| cycle4-all-alld-include_self | 0 | 0 | 1 |
| cycle4-all-alld-exclude_self | 0 | 0 | 1 |

Variance includes all cross-time covariance. EXACT.json retains every transition
row, labeled state, expected trajectory, covariance contribution and first-all-D mass.
Its restricted hitting time is E[min(T0,7)], not an eventual mean absorption time.

## Controls and boundaries

All six complete-graph controls match the existing Study 002 count benchmark exactly
for transitions, finite-horizon first/second moments, covariance-aware variance and
first-all-D probabilities under matched denominators and this eight-round horizon.
Sparse count projections are checked against every labeled state and rejected when
strong lumpability fails. The four-cycle witness is retained in EXACT.json and tests.

On the four-cycle with d fixed D, (1,1,0,0) gives next-count PMF
(1/8,3/8,3/8,1/8); (1,0,1,0) gives (0,1,0,0). Both start with two C.

Star hub/leaf placements change which actor is fixed AllD; they are separate design
conditions, not repetitions. Structure, population composition, placement and the
self-inclusion convention must remain explicit. No payoff outcome is inferred.

The rational independent Bernoulli assumption is idealized. The simulator retains
binary-float thresholds and finite-precision RNG draws. Real-observation tests find
the same local probability formula up to that explicitly acknowledged rounding.

No general topology ranking, eventual absorption theorem, human/LLM inference,
sampling uncertainty interval or new study freeze is supported by this readout.

## Source and regeneration

DESIGN.md declares the graphs, initialization, limits and moment recurrences.
EXACT.json records SHA-256 source commitments without timestamps or floats.
These establish consistency, not external publication or historical authenticity.
Existing Study 002 and graph execution provenance/readouts remain untouched.

Run with PYTHONPATH=src: python experiments/sparse-ptft/generate.py --check
or make check-sparse-ptft. Check mode byte-compares both outputs without writing.
