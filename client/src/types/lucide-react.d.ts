// client/src/types/lucide-react.d.ts
declare module 'lucide-react' {
  import * as React from 'react';

  export interface LucideProps extends React.SVGProps<SVGSVGElement> {
    size?: string | number;
    color?: string;
    strokeWidth?: string | number;
    absoluteStrokeWidth?: boolean;
    className?: string;
  }

  export type LucideIcon = React.ForwardRefExoticComponent<
    LucideProps & React.RefAttributes<SVGSVGElement>
  >;

  export const Zap: LucideIcon;
  export const MessageSquare: LucideIcon;
  export const MousePointer: LucideIcon;
  export const Users: LucideIcon;
  export const TrendingUp: LucideIcon;
  export const ArrowRight: LucideIcon;
  export const ArrowUpRight: LucideIcon;
  export const Plus: LucideIcon;
  export const ShieldCheck: LucideIcon;
  export const UserCheck: LucideIcon;
  export const Sparkles: LucideIcon;
  export const RefreshCw: LucideIcon;
  export const Clock: LucideIcon;
  export const Home: LucideIcon;
  export const BarChart2: LucideIcon;
  export const Instagram: LucideIcon;
  export const Settings: LucideIcon;
  export const ChevronDown: LucideIcon;
  export const Check: LucideIcon;
  export const Search: LucideIcon;
  export const Filter: LucideIcon;
  export const MoreVertical: LucideIcon;
  export const ArrowLeft: LucideIcon;
  export const Send: LucideIcon;
  export const Repeat: LucideIcon;
  export const AlertCircle: LucideIcon;
  export const CheckCircle: LucideIcon;
  export const X: LucideIcon;
  export const Play: LucideIcon;
  export const Pause: LucideIcon;
  export const Trash2: LucideIcon;
  export const Edit: LucideIcon;
  export const Copy: LucideIcon;
  export const ExternalLink: LucideIcon;
  export const Lock: LucideIcon;
  export const Eye: LucideIcon;
  export const Mail: LucideIcon;
  export const Bell: LucideIcon;
  export const UserPlus: LucideIcon;
  export const User: LucideIcon;
  export const Loader2: LucideIcon;
  export const Save: LucideIcon;
  export const ChevronRight: LucideIcon;
  export const Download: LucideIcon;
  export const Paperclip: LucideIcon;
  export const Smile: LucideIcon;
  export const CheckCheck: LucideIcon;
  export const CreditCard: LucideIcon;
  export const Shield: LucideIcon;
  export const Crown: LucideIcon;
  export const LogOut: LucideIcon;
  export const Calendar: LucideIcon;
  export const FileText: LucideIcon;
  export const Ban: LucideIcon;
  export const Edit2: LucideIcon;
  export const Edit3: LucideIcon;
  export const BookOpen: LucideIcon;
  export const Percent: LucideIcon;
  export const HelpCircle: LucideIcon;
  export const Gift: LucideIcon;
  export const Star: LucideIcon;
  export const ChevronLeft: LucideIcon;
  export const ChevronUp: LucideIcon;
  export const File: LucideIcon;
  export const Pencil: LucideIcon;
  export const Heart: LucideIcon;
  export const MessageCircle: LucideIcon;
  export const Bookmark: LucideIcon;
  export const MoreHorizontal: LucideIcon;
  export const Phone: LucideIcon;
  export const Video: LucideIcon;
  export const Info: LucideIcon;
  export const Image: LucideIcon;
  export const Globe: LucideIcon;
  export const Film: LucideIcon;
  export const Link2: LucideIcon;
  export const Share2: LucideIcon;
  export const ShoppingCart: LucideIcon;
  export const Radio: LucideIcon;
  export const AtSign: LucideIcon;
  export const Bot: LucideIcon;
  export const Sliders: LucideIcon;
  export const CornerDownRight: LucideIcon;
  export const Tag: LucideIcon;
  export const ArrowDown: LucideIcon;
  export const GripVertical: LucideIcon;
  export const Upload: LucideIcon;
  export const Hash: LucideIcon;
  export const Flag: LucideIcon;

  const icons: { [key: string]: LucideIcon };
  export default icons;
}
