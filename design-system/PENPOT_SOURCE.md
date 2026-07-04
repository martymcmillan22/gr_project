# Penpot Token Source Reference

## Source File
- **Penpot Project**: Tokens starter kit
- **File ID**: 13b17a96-57a4-8158-8008-42d193495fdc
- **Location**: /Users/martymcmillan/Downloads/Tokens starter kit.penpot
- **Last Synced**: 2026-07-01

## Token Groups (from Penpot)
- Typography (4 tokens)
- Dark - Base (9 component tokens)
- Density - Spacious
- Density - Compact
- Density - Comfortable
- Density - Modular Scales
- Foundations - Scales
- Foundations - Colors (200+ color tokens across 13 color families)
- Foundations - Fixed
- Linear Scale
- Modular Scale
- Light - Base (9 component tokens)
- Color theme - Muted
- Color theme - Vibrant
- $themes
- $metadata

**Total Tokens**: 577

## Color Palettes Extracted

### Primary (Blue)
- 050: #e4f2ff
- 100: #bee1ff
- 200: #81ccff
- 300: #00b4f8
- 400: #0094d4
- 500: #087eb4
- 600: #045982
- 700: #024567
- 800: #083550
- 900: #00263d
- 950: #00101d

### Neutral (BlueGray)
- 050: #fafbfc
- 100: #edf0f3
- 200: #d9dfe4
- 300: #b7bfc7
- 400: #99a3ae
- 500: #818c97
- 600: #57606a
- 700: #424a54
- 800: #303841
- 900: #222931
- 950: #10141a

### Accent (Purple)
- 050: #fefaff
- 100: #f5ecff
- 200: #e8d7ff
- 300: #cfb0ff
- 400: #b28ffa
- 500: #9777e8
- 600: #703fcc
- 700: #582ea3
- 800: #422281
- 900: #311666
- 950: #19083a

### Additional Palettes
- **Green**: 11 shades (050-950)
- **Orange**: 11 shades (050-950)
- **Pink**: 11 shades (050-950)

## How to Sync Updates

When you modify tokens in Penpot:

1. Export Penpot file as .penpot
2. Run: `node scripts/sync-penpot-tokens.js <path-to-file>`
3. This will:
   - Extract tokens.json from the Penpot file
   - Resolve all token references
   - Generate updated tokens.ts
   - Update all component mappings

## Component Usage

All tokens are available via:
```typescript
import { tokens } from '@/design-system/tokens';

// Usage
const color = tokens.colors.primary['600'];  // #045982
const space = tokens.spacing.md;              // 1rem
const fontSize = tokens.typography.body.base.fontSize;  // 1rem
```
