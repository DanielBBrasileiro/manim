## Reference-Native Production

This flow lets AIOX use a translated reference as active creative direction during production.

### Existing reference contract

```bash
python3 aiox.py create briefings/my_brief.yaml --reference worldquantfoundry_com
```

### ZIP-first production

```bash
python3 aiox.py create briefings/my_brief.yaml \
  --reference-zip /path/to/site_snapshot.zip \
  --reference-screenshot /path/to/homepage.png \
  --reference-notes "Borrow spacing calm, avoid literal hero composition."
```

The ZIP path will:
- ingest the site snapshot
- write a translated reference contract to `contracts/references/`
- attach the translated reference to the current production briefing
- resolve style direction for still and motion outputs

### What the reference influences

Reference-native direction can guide:
- `style_pack`
- `typography_system`
- `still_family`
- `motion_grammar`
- `negative_space_target`
- `accent_intensity`
- `grain` / material feel

Explicit briefing overrides still win.

### Multi-output use

Use one shared briefing with multiple targets, for example:

```yaml
output_targets:
  - linkedin_feed_4_5
  - short_cinematic_vertical
  - youtube_essay_16_9
```

The same reference-native direction will be shared across outputs, while target-specific overrides adapt still, motion, and editorial/technical variants.
