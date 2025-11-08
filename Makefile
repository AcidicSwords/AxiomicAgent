PY := python

.PHONY: test run build-mit build-yt scrub-convo build-convo

test:
	$(PY) -m pytest -q

run:
	$(PY) -m pipeline.run --manifest manifests/curriculum_conversation_example.json

build-mit:
	$(PY) -m pipeline.curriculum.build_mit

build-yt:
	@echo "Use pipeline.curriculum.normalize_youtube_playlist + build_youtube per manifest entries"

scrub-convo:
	$(PY) -m pipeline.conversation.scrub_transcripts --input-dir RawConversation --out-dir reports/conversation_clean

build-convo:
	$(PY) -m pipeline.conversation.build_datasets --input-dir reports/conversation_clean --output-dir datasets/mit_curriculum_datasets --window-size 6

