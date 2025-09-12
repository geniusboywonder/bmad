# BotArmy Style Guide

This document provides a comprehensive overview of the BotArmy POC application's design system, including the color palette, typography, and usage guidelines.

## Technology Stack

### Frontend Framework
- **Next.js**: 15.5.2 with App Router
- **React**: 19.x (latest stable)
- **TypeScript**: 5.x (strict mode enabled)

### Styling & UI
- **Tailwind CSS**: 3.4.17 (stable version for better CSS variable compatibility)
- **PostCSS**: 8.5.6 with Autoprefixer 10.4.21
- **shadcn/ui**: Radix UI components with Tailwind styling
- **CSS Variables**: HSL color format for theme system

### Configuration Files
- `tailwind.config.js`: Tailwind v3 configuration with extended color palette
- `postcss.config.mjs`: PostCSS configuration for Tailwind and Autoprefixer
- `app/globals.css`: Global styles with CSS custom properties

## Color System

The application uses a comprehensive theming system with CSS variables defined in `app/globals.css`. All colors are defined as HSL values in CSS custom properties and exposed through Tailwind CSS utility classes configured in `tailwind.config.js`.

### Base Palette

#### Light Theme

| Color Swatch | Color Name | Hex (Approximated) |
| :--- | :--- | :--- |
| <div style="width:100%;height:20px;background-color:#ffffff;border:1px solid #000;"></div> | `background` | `#ffffff` |
| <div style="width:100%;height:20px;background-color:#202b38;"></div> | `foreground` | `#202b38` |
| <div style="width:100%;height:20px;background-color:#fafafa;border:1px solid #ccc;"></div> | `card` | `#fafafa` |
| <div style="width:100%;height:20px;background-color:#0891b2;"></div> | `primary` | `#0891b2` |
| <div style="width:100%;height:20px;background-color:#f3f4f6;border:1px solid #ccc;"></div> | `secondary` | `#f3f4f6` |
| <div style="width:100%;height:20px;background-color:#6b7280;"></div> | `muted-foreground` | `#6b7280` |
| <div style="width:100%;height:20px;background-color:#ef4444;"></div> | `destructive` | `#ef4444` |
| <div style="width:100%;height:20px;background-color:#e5e7eb;border:1px solid #ccc;"></div> | `border` | `#e5e7eb` |

#### Dark Theme

| Color Swatch | Color Name | Hex (Approximated) |
| :--- | :--- | :--- |
| <div style="width:100%;height:20px;background-color:#1f2937;"></div> | `background` | `#1f2937` |
| <div style="width:100%;height:20px;background-color:#ffffff;border:1px solid #000;"></div> | `foreground` | `#ffffff` |
| <div style="width:100%;height:20px;background-color:#164e63;"></div> | `card` | `#164e63` |
| <div style="width:100%;height:20px;background-color:#06b6d4;"></div> | `primary` | `#06b6d4` |
| <div style="width:100%;height:20px;background-color:#374151;"></div> | `secondary` | `#374151` |
| <div style="width:100%;height:20px;background-color:#9ca3af;"></div> | `muted-foreground` | `#9ca3af` |
| <div style="width:100%;height:20px;background-color:#dc2626;"></div> | `destructive` | `#dc2626` |
| <div style="width:100%;height:20px;background-color:#374151;"></div> | `border` | `#374151` |

### Semantic Colors

These colors are used to convey meaning and represent different roles and message types in the application.

#### Status Colors (for task/artifact states)

| Color Swatch | Color Name | Tailwind Class | Usage |
| :--- | :--- | :--- | :--- |
| <div style="width:100%;height:20px;background-color:#10b981;"></div> | Green (Tester) | `text-tester` | Done/Completed states |
| <div style="width:100%;height:20px;background-color:#3b82f6;"></div> | Blue (Analyst) | `text-analyst` | WIP/In-Progress states |
| <div style="width:100%;height:20px;background-color:#f59e0b;"></div> | Amber | `text-amber` | Waiting/Pending states |
| <div style="width:100%;height:20px;background-color:#9333ea;"></div> | Purple | `text-purple-600` | Queued/Ready states |
| <div style="width:100%;height:20px;background-color:#64748b;"></div> | Slate | `text-slate-600` | Planned/Scheduled states |
| <div style="width:100%;height:20px;background-color:#ef4444;"></div> | Red (Destructive) | `text-destructive` | Error/Failed states |

#### Stage/Agent Colors (for roles and stages)

| Color Swatch | Color Name | Tailwind Class | Stage/Agent | Visual Distinction |
| :--- | :--- | :--- | :--- | :--- |
| <div style="width:100%;height:20px;background-color:#64748b;"></div> | Slate | `text-slate-500` | Plan/Analyst | Different from white focus |
| <div style="width:100%;height:20px;background-color:#ec4899;"></div> | Pink | `text-pink-500` | Design/Architect | Completely unique |
| <div style="width:100%;height:20px;background-color:#65a30d;"></div> | Lime | `text-lime-600` | Build/Developer | Perfect shade difference from status green |
| <div style="width:100%;height:20px;background-color:#0ea5e9;"></div> | Sky | `text-sky-500` | Validate/Tester | Different shade from status blue |
| <div style="width:100%;height:20px;background-color:#e11d48;"></div> | Rose | `text-rose-600` | Launch/Deployer | Far from purple queued |

#### Alert Colors (for notifications)

| Color Swatch | Color Name | Tailwind Class | Usage |
| :--- | :--- | :--- | :--- |
| <div style="width:100%;height:20px;background-color:#f59e0b;"></div> | Amber | `text-amber` | HITL alerts and warnings |
| <div style="width:100%;height:20px;background-color:#0891b2;"></div> | User | `user` | User messages |
| <div style="width:100%;height:20px;background-color:#f3f4f6;border:1px solid #ccc;"></div> | System | `system` | System notifications |
| <div style="width:100%;height:20px;background-color:#14b8a6;"></div> | Teal | `teal` | General highlights |

## Technical Implementation

### CSS Custom Properties Format

Colors are defined in `app/globals.css` using HSL format without the `hsl()` wrapper:

```css
:root {
  --background: 0 0% 100%;           /* White */
  --foreground: 222.2 84% 4.9%;      /* Dark slate */
  --primary: 188 100% 37%;           /* Cyan-600 */
  --border: 214.3 31.8% 91.4%;       /* Slate-200 */
  /* ... */
}

.dark {
  --background: 222.2 84% 4.9%;      /* Dark slate */
  --foreground: 210 40% 98%;         /* Light gray */
  --primary: 187 92% 44%;            /* Cyan-500 */
  /* ... */
}
```

### Tailwind Configuration

Colors are mapped in `tailwind.config.js` using the `hsl()` function:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... extended palette
      }
    }
  }
}
```

## Usage Guidelines

### Color Application

All colors should be applied using the Tailwind CSS utility classes defined in `tailwind.config.js`. **Do not use hardcoded hex values or inline styles.**

#### Basic Usage

```html
<!-- Primary button -->
<button class="bg-primary text-primary-foreground hover:bg-primary/90">
  Click me
</button>

<!-- Card with border -->
<div class="bg-card border border-border rounded-lg p-4">
  Card content
</div>
```

#### Agent-Specific Colors

```html
<!-- Analyst agent message -->
<div class="bg-analyst/10 border border-analyst/20 text-analyst rounded-lg p-3">
  Analysis complete: Found 5 requirements
</div>

<!-- Developer agent status -->
<span class="bg-developer/10 text-developer px-2 py-1 rounded-full text-xs">
  Coding in progress
</span>
```

#### Opacity Modifiers

Use Tailwind's opacity modifiers for subtle backgrounds and effects:

```html
<!-- Light background -->
<div class="bg-primary/10">Light primary background</div>

<!-- Hover states -->
<button class="bg-secondary hover:bg-secondary/80">Hover effect</button>
```

### Best Practices

1. **Always use CSS variables**: Never hardcode color values
2. **Respect the theme system**: Colors automatically adapt to light/dark themes
3. **Use semantic names**: Prefer `bg-primary` over `bg-cyan-600`
4. **Leverage opacity**: Use `/10`, `/20`, etc. for subtle backgrounds
5. **Test in both themes**: Ensure components work in light and dark modes

## Tab Component Standards

### Tab Design Principles

The tab component follows traditional browser tab patterns for optimal user experience and accessibility.

### Visual Specifications

#### Tab List Structure
- **Container**: Transparent background with bottom border
- **Layout**: Horizontal flex layout with items aligned to bottom
- **Spacing**: No padding around the tab list container

#### Individual Tabs
- **Inactive State**:
  - Background: Transparent
  - Text: `text-muted-foreground` with hover to `text-foreground`
  - Border: Transparent top/left/right borders
  - Hover: `bg-muted/50` background overlay
  
- **Active State**:
  - Background: `bg-background` (matches content area)
  - Text: `text-foreground`
  - Border: `border-border` for top/left/right, `border-b-background` to connect seamlessly with content
  - Shadow: `shadow-sm` for subtle elevation

#### Tab Content Area
- **Background**: `bg-background` 
- **Border**: `border-border` on all sides except top
- **Border Radius**: `rounded-b-lg rounded-tr-lg` (rounded bottom corners and top-right)
- **Padding**: `p-4` default, customizable via className
- **Connection**: Border-top removed to create seamless connection with active tab

### Usage Guidelines

#### Basic Implementation
```tsx
<Tabs defaultValue="progress" className="w-full">
  <TabsList className="mb-0">
    <TabsTrigger value="progress">Progress</TabsTrigger>
    <TabsTrigger value="config">Configuration</TabsTrigger>
  </TabsList>

  <TabsContent value="progress" className="space-y-6 p-6">
    {/* Progress content */}
  </TabsContent>

  <TabsContent value="config" className="p-6">
    {/* Configuration content */}
  </TabsContent>
</Tabs>
```

#### Styling Customizations
- **TabsList**: Remove default margin with `mb-0` for seamless connection
- **TabsContent**: Add custom padding as needed (default `p-4` is applied)
- **Responsive**: Tabs automatically adapt to container width

#### Accessibility Features
- Full keyboard navigation support
- ARIA labels and roles provided by Radix UI
- Focus indicators with `focus-visible:ring-2 focus-visible:ring-primary/20`
- Proper color contrast ratios maintained

## Badge Component System

### Badge Variants & Sizing

BotArmy uses an enhanced badge component system with optimized variants for better visual hierarchy and consistency across the application.

#### Badge Variants

| Variant | Usage | Visual Appearance |
|---------|-------|------------------|
| `default` | Primary actions/states | Filled with primary color |
| `secondary` | Secondary information | Filled with muted background |
| `destructive` | Errors/critical states | Red background with white text |
| `outline` | Neutral/bordered tags | Transparent with border |
| **`muted`** | **Small status tags** | **Minimal, subtle appearance** |

#### Badge Sizes

| Size | Usage | Styling |
|------|-------|---------|
| `default` | Standard badges | `px-2 py-0.5 text-xs` |
| **`sm`** | **Compact status tags** | **`px-1 py-0.5 text-[10px] h-4`** |

### Standard Badge Implementation

**ALL badges must use the centralized management system** for consistency:

```tsx
// REQUIRED - Import centralized functions
import { getStatusBadgeClasses, getAgentBadgeClasses } from "@/lib/utils/badge-utils";

// Status badges - Standard pattern
<Badge variant="muted" size="sm" className={getStatusBadgeClasses(status)}>
  {status.toUpperCase()}
</Badge>

// Agent badges - Standard pattern
<Badge variant="muted" size="sm" className={getAgentBadgeClasses(agent)}>
  <Icon className="w-2.5 h-2.5 mr-0.5" />
  {agent}
</Badge>

// Critical states only - Use destructive variant
<Badge variant="destructive" size="sm">HITL</Badge>
```

#### Visual Characteristics
- **Base Style**: `variant="muted" size="sm"` - provides `text-[10px] px-1 py-0.5 h-4`
- **Colors**: Applied automatically by centralized functions
- **Icons**: `w-2.5 h-2.5 mr-0.5` - optimized for small badges
- **Consistency**: All badges use identical sizing and behavior

## Centralized Badge Management System

**CRITICAL**: All badges must use the centralized color management system located at `@/lib/utils/badge-utils.ts`. This ensures consistency across the entire application and eliminates color duplication.

### Import and Usage

```tsx
import { getStatusBadgeClasses, getAgentBadgeClasses } from "@/lib/utils/badge-utils";

// Status badges
<Badge variant="muted" size="sm" className={getStatusBadgeClasses(status)}>
  {status.toUpperCase()}
</Badge>

// Agent badges  
<Badge variant="muted" size="sm" className={getAgentBadgeClasses(agent)}>
  <Icon className="w-2.5 h-2.5 mr-0.5" />
  {agent}
</Badge>
```

### Status Color Mapping

The centralized system provides consistent colors for all status types:

| Status | Color | CSS Class | Visual |
|--------|-------|-----------|---------|
| `done`, `completed`, `finished` | Green | `text-tester border-tester/20` | ✅ |
| `wip`, `in-progress`, `active` | Blue | `text-analyst border-analyst/20` | 🔄 |
| `waiting`, `pending` | Amber | `text-amber border-amber/20` | ⏳ |
| `queued`, `ready` | Purple | `text-purple-600 border-purple-600/20` | 📋 |
| `planned`, `scheduled` | Slate | `text-slate-600 border-slate-600/20` | 📅 |
| `error`, `failed`, `blocked` | Red | `text-destructive border-destructive/20` | ❌ |

### Stage/Agent Color Mapping

The new stage color system provides complete visual separation from status colors:

| Stage/Agent | Color | CSS Class | Background Class | Visual |
|-------------|-------|-----------|------------------|---------|
| `analyst` (Plan) | Slate | `text-slate-500 border-slate-500/20` | `bg-slate-500/5` | 🔘 |
| `architect` (Design) | Pink | `text-pink-500 border-pink-500/20` | `bg-pink-500/5` | 🌸 |
| `developer` (Build) | Lime | `text-lime-600 border-lime-600/20` | `bg-lime-600/5` | 🟢 |
| `tester` (Validate) | Sky | `text-sky-500 border-sky-500/20` | `bg-sky-500/5` | ☁️ |
| `deployer` (Launch) | Rose | `text-rose-600 border-rose-600/20` | `bg-rose-600/5` | 🌹 |
| `hitl` | Amber | `text-amber border-amber/20` | `bg-amber/5` | ⚠️ |

## Color System Design Principles

### Complete Visual Separation

The BotArmy color system uses **three distinct color families** to prevent confusion:

1. **Status Colors**: For task/artifact states (done, wip, waiting, etc.)
2. **Stage/Agent Colors**: For roles and workflow stages (analyst, architect, etc.)  
3. **Alert Colors**: For notifications and user interactions (HITL, warnings)

### Key Design Decisions

- **No Overlap**: Status and stage colors are completely separate families
- **Consistent Shades**: Each color group uses similar saturation levels (like lime vs green)
- **Accessibility**: All colors maintain proper contrast ratios in both light/dark themes
- **Semantic Meaning**: Colors align with their conceptual purpose (e.g., rose for deployment)

### Visual Hierarchy

```
🔴 CRITICAL: Red for errors and failures
🟠 URGENT: Amber for HITL alerts and waiting states  
🟡 CAUTION: Yellow tones for attention-needed states
🟢 SUCCESS: Green shades for completion and growth
🔵 ACTIVE: Blue family for work-in-progress states
🟣 PLANNED: Purple for queued and future items
⚫ NEUTRAL: Gray family for planned and inactive states
🌸 UNIQUE: Pink, Sky, Rose for distinct stage identification
```

### Benefits of Centralized System

1. **Consistency**: All badges use the same color logic
2. **Maintainability**: Colors managed in one location
3. **Type Safety**: TypeScript types for status and agent values
4. **Extensibility**: Easy to add new statuses or agents
5. **Performance**: No duplicate color logic across components
6. **Accessibility**: Guaranteed contrast and theme compatibility

### Development Guidelines

#### Badge Implementation Rules

1. **NEVER hardcode badge colors** - Always use `getStatusBadgeClasses()` or `getAgentBadgeClasses()`
2. **Consistent sizing** - Always use `variant="muted" size="sm"` for status/agent badges
3. **Icon sizing** - Use `w-2.5 h-2.5 mr-0.5` for icons in small badges
4. **Import pattern** - Always import from `@/lib/utils/badge-utils`

#### Adding New Status Types

To add a new status, update `@/lib/utils/badge-utils.ts`:

```tsx
export const getStatusBadgeClasses = (status: BadgeStatus | string): string => {
  switch (status.toLowerCase()) {
    // ... existing cases
    case 'new-status':
      return 'text-purple-500 border-purple-500/20';
    default:
      return 'text-muted-foreground border-muted-foreground/20';
  }
};
```

#### Quality Assurance

- **No duplicate color logic** - All badge colors in one place
- **TypeScript safety** - Use provided types for status and agent values
- **Visual consistency** - All badges use identical base styling
- **Accessibility** - Colors maintain proper contrast ratios in both themes

## Badge System Summary

The BotArmy badge system has been completely modernized with:

✅ **Centralized Management**: All colors managed in `@/lib/utils/badge-utils.ts`  
✅ **Consistent Sizing**: `variant="muted" size="sm"` provides perfect proportions  
✅ **Full Color Coverage**: Distinct colors for all status types including QUEUED and PLANNED  
✅ **TypeScript Safety**: Type-safe status and agent values  
✅ **Zero Duplication**: Single source of truth for all badge styling  

### Quick Reference

```tsx
// The only badge patterns you need:
import { getStatusBadgeClasses, getAgentBadgeClasses } from "@/lib/utils/badge-utils";

// Status badge
<Badge variant="muted" size="sm" className={getStatusBadgeClasses(status)}>
  {status.toUpperCase()}
</Badge>

// Agent badge
<Badge variant="muted" size="sm" className={getAgentBadgeClasses(agent)}>
  <Icon className="w-2.5 h-2.5 mr-0.5" />
  {agent}
</Badge>

// Critical only
<Badge variant="destructive" size="sm">HITL</Badge>
```

## Notification System Enhancement

### Expandable Alert Components

The notification system has been enhanced with expandable alerts that provide better user experience and visual hierarchy.

#### Implementation Pattern

```tsx
// Enhanced notification with expandable functionality
{visibleAlerts.map((alert) => {
  const isExpanded = expandedAlerts.includes(alert.id)
  const stageName = alert.id.includes('arch') ? 'Architecture' : 'Testing'
  const shortMessage = `[⚠️] ${stageName}`
  
  return (
    <div className="group flex items-center space-x-2 bg-background/90 backdrop-blur-sm border border-amber/30 rounded-lg px-3 py-2 shadow-sm">
      <button onClick={() => toggleExpanded(alert.id)}>
        <span>{isExpanded ? alert.message : shortMessage}</span>
        <ChevronDown className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
      </button>
      <Button onClick={() => dismissAlert(alert.id)}>
        <X className="w-3 h-3" />
      </Button>
    </div>
  )
})}
```

#### Visual Specifications

- **Collapsed State**: Shows `[⚠️] Stage name` format
- **Expanded State**: Shows full message text
- **Hover Effects**: Smooth transitions with backdrop blur
- **Dismiss Functionality**: X button appears on hover
- **Gradient Background**: `bg-gradient-to-r from-amber/90 to-amber/70`

## Activity Timeline Component Enhancement

### Enhanced Visual Treatment

The Activity Timeline has been completely redesigned with modern visual hierarchy and interactive elements.

#### Key Improvements

1. **Gradient Backgrounds**: `bg-gradient-to-br from-card to-card/90`
2. **Enhanced Timeline Dots**: Larger dots with gradient backgrounds and ring effects
3. **Hover Interactions**: Scale effects and color transitions
4. **Better Spacing**: Improved padding and gap management
5. **Status Integration**: Using centralized badge system

#### Implementation

```tsx
<Card className="shadow-sm border-2 border-border/50 bg-gradient-to-br from-card to-card/90">
  <CardHeader className="border-b border-border/50">
    <CardTitle className="flex items-center gap-2">
      <div className="w-1 h-6 bg-teal rounded-full"></div>
      Recent Activities
    </CardTitle>
  </CardHeader>
  {/* Enhanced timeline items with hover effects */}
</Card>
```

## System Health Indicator Enhancement

### Modern Badge-Based Design

The system health indicator has been redesigned to use the centralized badge system with enhanced visual feedback.

#### New Implementation

```tsx
<Badge 
  variant="muted" 
  size="sm" 
  className={cn(
    "flex items-center gap-1.5 px-2 py-1",
    getStatusBadgeClasses(status === 'healthy' ? 'completed' : status === 'degraded' ? 'waiting' : 'error')
  )}
>
  {getStatusIcon(status)}
  <span className="font-medium">{getStatusText(status)}</span>
</Badge>
```

#### Status Mapping

- **Healthy**: Green with Wifi icon
- **Degraded**: Amber with Alert Triangle icon  
- **Unhealthy**: Red with WifiOff icon
- **Responsive**: Hidden on small screens (`hidden md:flex`)

## Process Summary Flow Enhancement

### Connecting Lines and Progress Indicators

The process summary stage flow now includes visual connecting lines that show progress and relationships between stages.

#### Enhanced Stage Flow

```tsx
<div className="relative flex items-center justify-between gap-1 px-2">
  {/* Background connecting line */}
  <div className="absolute top-[28px] left-8 right-8 h-0.5 bg-gradient-to-r from-border via-teal/30 to-border -z-10"></div>
  
  {/* Enhanced stage buttons with progress indicators */}
  {stagesData.map((stage, index) => (
    <button className="relative z-10 shadow-lg">
      <div className="w-12 h-12 rounded-full border-2 border-background shadow-sm">
        {/* Stage content */}
      </div>
    </button>
  ))}
</div>
```

#### Visual Enhancements

- **Gradient Progress Line**: Shows completion status across stages
- **Enhanced Shadows**: Better depth and visual hierarchy
- **Status Overlays**: Improved positioning and visibility
- **Interactive States**: Better hover and selection feedback

## Chat Interface Resizing Fix

### Dynamic Height Management

The chat interface now properly handles resizable states with the input area included in all resize operations.

#### Key Changes

```tsx
// Dynamic height based on resizable state
<div className={cn(
  "overflow-hidden flex-1",
  !isResizable && "h-80"
)}>
  {/* Chat content */}
</div>

// Flex-shrink-0 for input area
<div className="p-2 flex-shrink-0">
  {/* Input controls */}
</div>
```

## Updated Development Guidelines

### Component Enhancement Patterns

1. **Progressive Enhancement**: Start with basic functionality, add visual enhancements
2. **Centralized Systems**: Use badge utilities, status functions, and design tokens
3. **Responsive Design**: Consider mobile-first with appropriate breakpoints
4. **Interactive Feedback**: Include hover states, transitions, and loading states
5. **Accessibility**: Maintain semantic HTML and proper ARIA labels

### Performance Considerations

- **Backdrop Blur**: Use sparingly for performance
- **Gradient Backgrounds**: Prefer CSS gradients over complex SVGs
- **Animation Timing**: Use consistent timing (150-300ms)
- **Z-Index Management**: Use logical stacking contexts

### Development Notes

- **Tailwind v3**: Using stable version for better CSS variable compatibility
- **HSL Format**: Provides better color manipulation and theme transitions  
- **No v4 Migration**: v4 had compatibility issues with the existing color system
- **Browser Support**: HSL custom properties work in all modern browsers
- **Tab Component**: Based on Radix UI Tabs primitive with custom styling for traditional browser tab appearance
- **Badge System**: Fully centralized and type-safe as of latest update
- **Enhanced Components**: All major dashboard components updated with modern visual treatments
