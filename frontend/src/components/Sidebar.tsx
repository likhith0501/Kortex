import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, FileText, Compass, GitCompare, Share2, 
  Settings as SettingsIcon, BookOpen, ChevronLeft, ChevronRight, 
  Sun, Moon, Layers
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

interface SidebarProps {
  totalPapers?: number;
  totalGaps?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ totalPapers = 0, totalGaps = 0 }) => {
  const [collapsed, setCollapsed] = useState(false);
  const theme = useAppStore((s) => s.theme);
  const toggleTheme = useAppStore((s) => s.toggleTheme);
  const comparisonCount = useAppStore((s) => s.comparisonPaperIds.length);

  const navItems = [
    {
      to: '/dashboard',
      label: 'Cockpit Dashboard',
      icon: LayoutDashboard,
    },
    {
      to: '/library',
      label: 'Research Library',
      icon: FileText,
      badge: totalPapers > 0 ? totalPapers : undefined,
    },
    {
      to: '/analysis',
      label: 'Paper Analysis',
      icon: BookOpen,
    },
    {
      to: '/recommendations',
      label: 'Recommendations & Graph',
      icon: Share2,
    },
    {
      to: '/gaps',
      label: 'Research Gaps',
      icon: Compass,
      badge: totalGaps > 0 ? totalGaps : undefined,
    },
    {
      to: '/compare',
      label: 'Comparison Workspace',
      icon: GitCompare,
      badge: comparisonCount > 0 ? `${comparisonCount} sel` : undefined,
      badgeColor: 'bg-accent-violet/20 text-accent-violet border-accent-violet/30',
    },
    {
      to: '/reports',
      label: 'Reports & Export',
      icon: Layers,
    },
    {
      to: '/settings',
      label: 'Settings & Health',
      icon: SettingsIcon,
    },
  ];

  return (
    <aside className={`relative flex flex-col h-screen bg-surface border-r border-border transition-all duration-200 select-none ${
      collapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Brand Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-border">
        {!collapsed ? (
          <div className="flex items-center gap-2.5 truncate">
            <div className="w-8 h-8 rounded-control bg-gradient-to-br from-accent-primary via-accent-cyan to-accent-violet flex items-center justify-center text-white font-bold text-sm shadow-sm">
              KX
            </div>
            <div className="truncate">
              <h1 className="text-sm font-semibold tracking-tight text-text-primary">
                KORTEX
              </h1>
              <p className="text-[10px] text-text-muted truncate">
                Autonomous Intelligence
              </p>
            </div>
          </div>
        ) : (
          <div className="w-8 h-8 mx-auto rounded-control bg-gradient-to-br from-accent-primary via-accent-cyan to-accent-violet flex items-center justify-center text-white font-bold text-xs shadow-sm">
            KX
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-raised transition-colors"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-control text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-raised text-accent-cyan font-semibold border border-accent-cyan/30 shadow-sm'
                    : 'text-text-secondary hover:text-text-primary hover:bg-raised/50'
                } ${collapsed ? 'justify-center px-0' : ''}`
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!collapsed && (
                <>
                  <span className="truncate flex-1">{item.label}</span>
                  {item.badge !== undefined && (
                    <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                      item.badgeColor || 'bg-base text-accent-cyan border-border'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Footer Actions */}
      <div className="p-3 border-t border-border flex flex-col gap-2">
        <button
          onClick={toggleTheme}
          className={`flex items-center gap-3 px-3 py-2 rounded-control text-xs text-text-secondary hover:text-text-primary hover:bg-raised transition-colors ${
            collapsed ? 'justify-center px-0' : ''
          }`}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-warning shrink-0" />
          ) : (
            <Moon className="w-4 h-4 text-accent-violet shrink-0" />
          )}
          {!collapsed && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
        </button>

        {!collapsed && (
          <div className="px-2 py-1.5 rounded bg-raised/50 border border-border text-[10px] text-text-muted">
            <span className="font-mono text-accent-cyan">100% Offline Mode</span>
            <span className="block truncate">Local NLP • Zero Paid APIs</span>
          </div>
        )}
      </div>
    </aside>
  );
};
