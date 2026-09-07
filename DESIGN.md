# Design System: Invisible Accountant (UK MTD)

## Core Philosophy
- **Art Gallery Airy:** Extensive use of negative space, giving content room to breathe and framing data as high-value art.
- **Cinematic Choreography:** Smooth, deliberate interactions. No abrupt transitions.
- **Understated Elegance:** Sophisticated, reserved, and refined. Absolutely no Silicon Valley flash, and no neon glows.
- **Institutional Trust:** Conveying stability, legacy, and credibility through classic, authoritative styling.
- **High-competence Layout:** Asymmetric but highly ordered grid systems that project rigorous capability.

## Typography
- **Primary Font:** Geist (for highly legible UI/data) or Cabinet Grotesk (for structural headings) - rigorous, exact, and authoritative. NO Inter.
- **Scale:**
  - `h1`: 3rem, tight tracking (-0.02em), medium weight.
  - `h2`: 2.25rem, tight tracking (-0.01em).
  - `body`: 1rem, comfortable line-height (1.6), highly legible.
  - `caption`: 0.875rem, slightly muted.

## Color Palette (UK Institutional Trust)
- **Backgrounds:** Crisp White (`#FFFFFF`) or Off-White (`#F9FAFB`) - NO pure black.
- **Typography/Foreground:** Deep Slate (`#1E293B`) or Oxford Blue (`#0F172A`) for text - NO pure black text (`#000000`).
- **Accents:** 
  - Heritage Blue (`#1D4ED8`) for primary actions.
  - Subtle Silver/Gray (`#94A3B8`) for borders and secondary architectural elements.
- **Prohibited:** Gradients, neon colors, pure blacks. Solid, confident colors only.

## Spacing & Layout
- **Grid:** Asymmetric but highly ordered 12-column grid.
- **Padding/Margins:** Use large, deliberate spacing (e.g., `48px`, `64px`, `96px` blocks) to achieve the 'Art Gallery' feel.
- **Borders:** Thin, precise 1px borders in Subtle Silver (`#E2E8F0`) to separate sections without heavy lines.
- **Shadows:** Extremely soft, diffuse shadows only if necessary for depth; flat, structural design is preferred. No harsh drop shadows.

## Components
### Buttons
- **Primary:** Oxford Blue background, Crisp White text. Sharp corners or very subtle rounding (2px). No pill shapes. Hover effect: slight opacity change or deepen to a darker blue. No scaling or bouncing.
- **Secondary:** Transparent background, Oxford Blue text, 1px Oxford Blue border.

### Cards & Panels
- White backgrounds, thin gray borders, copious internal padding (`32px` or `40px`).
- Asymmetrical alignment of content within cards (e.g., headers flush left, contextual data visualization shifted right).

### Data Tables (MTD Context)
- **Alignment:** Numbers flush right, text flush left.
- **Headers:** Muted slate, uppercase, wide tracking (0.05em).
- **Rows:** Generous vertical padding, subtle bottom borders. Zebra striping is discouraged.

## Interaction & Motion (Cinematic Choreography)
- **Durations:** 300ms - 500ms for state changes.
- **Easing:** Custom Cubic Bezier (e.g., `cubic-bezier(0.2, 0.8, 0.2, 1)`) for a smooth, deliberate feel.
- **Transitions:** Opacity fades and subtle vertical translations (`y: 4px` to `0`) on load. No bouncy, elastic, or playful animations.
