'use client';

import { useState } from 'react';
import { Download, FileSpreadsheet, FileJson, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api/client';

// ============================================
// Types
// ============================================

export type ExportFormat = 'csv' | 'json';

export type ExportType =
  | 'portfolio'
  | 'watchlist'
  | 'screening_results'
  | 'tax_report'
  | 'trade_journal'
  | 'stock_analysis';

interface ExportButtonProps {
  exportType: ExportType;
  data: Record<string, unknown>;
  filename?: string;
  className?: string;
  variant?: 'default' | 'icon' | 'dropdown';
  availableFormats?: ExportFormat[];
}

// ============================================
// Export Button Component
// ============================================

/**
 * Export button with format selection
 */
export function ExportButton({
  exportType,
  data,
  filename,
  className,
  variant = 'default',
  availableFormats = ['csv', 'json'],
}: ExportButtonProps) {
  const [showDropdown, setShowDropdown] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportedFormat, setExportedFormat] = useState<ExportFormat | null>(null);

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(true);
    setShowDropdown(false);

    try {
      const endpoint = getExportEndpoint(exportType);
      const response = await api.post(endpoint, data, {
        params: { format },
        responseType: 'blob',
      });

      // Get filename from header or generate one
      const contentDisposition = response.headers['content-disposition'];
      let downloadFilename = filename;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=(.+)/);
        if (match) {
          downloadFilename = match[1];
        }
      }
      if (!downloadFilename) {
        downloadFilename = `${exportType}_export.${format}`;
      }

      // Create download link
      const blob = new Blob([response.data], {
        type: format === 'csv' ? 'text/csv' : 'application/json',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = downloadFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setExportedFormat(format);
      setTimeout(() => setExportedFormat(null), 2000);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  if (variant === 'icon') {
    return (
      <div className="relative">
        <Button
          variant="ghost"
          size="icon"
          className={cn('h-8 w-8', className)}
          onClick={() => setShowDropdown(!showDropdown)}
          disabled={isExporting}
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : exportedFormat ? (
            <Check className="h-4 w-4 text-emerald-400" />
          ) : (
            <Download className="h-4 w-4" />
          )}
        </Button>

        {showDropdown && (
          <FormatDropdown
            formats={availableFormats}
            onSelect={handleExport}
            onClose={() => setShowDropdown(false)}
          />
        )}
      </div>
    );
  }

  if (variant === 'dropdown') {
    return (
      <div className={cn('relative', className)}>
        <Button
          variant="outline"
          size="sm"
          className="border-slate-600"
          onClick={() => setShowDropdown(!showDropdown)}
          disabled={isExporting}
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : exportedFormat ? (
            <Check className="h-4 w-4 mr-2 text-emerald-400" />
          ) : (
            <Download className="h-4 w-4 mr-2" />
          )}
          Export
        </Button>

        {showDropdown && (
          <FormatDropdown
            formats={availableFormats}
            onSelect={handleExport}
            onClose={() => setShowDropdown(false)}
          />
        )}
      </div>
    );
  }

  // Default: single button that exports to CSV
  return (
    <Button
      variant="outline"
      size="sm"
      className={cn('border-slate-600', className)}
      onClick={() => handleExport('csv')}
      disabled={isExporting}
    >
      {isExporting ? (
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      ) : exportedFormat ? (
        <Check className="h-4 w-4 mr-2 text-emerald-400" />
      ) : (
        <Download className="h-4 w-4 mr-2" />
      )}
      Export CSV
    </Button>
  );
}

// ============================================
// Format Dropdown
// ============================================

function FormatDropdown({
  formats,
  onSelect,
  onClose,
}: {
  formats: ExportFormat[];
  onSelect: (format: ExportFormat) => void;
  onClose: () => void;
}) {
  const formatConfig: Record<ExportFormat, { label: string; icon: typeof FileSpreadsheet }> = {
    csv: { label: 'CSV (Spreadsheet)', icon: FileSpreadsheet },
    json: { label: 'JSON (Data)', icon: FileJson },
  };

  return (
    <>
      <div className="fixed inset-0 z-10" onClick={onClose} />
      <div className="absolute right-0 top-full mt-1 z-20 w-48 bg-slate-800 border border-slate-700 rounded-md shadow-lg py-1">
        <div className="px-3 py-2 text-xs font-medium text-slate-400 border-b border-slate-700">
          Export as
        </div>
        {formats.map((format) => {
          const config = formatConfig[format];
          const Icon = config.icon;
          return (
            <button
              key={format}
              className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700 flex items-center gap-2"
              onClick={() => onSelect(format)}
            >
              <Icon className="h-4 w-4 text-slate-400" />
              {config.label}
            </button>
          );
        })}
      </div>
    </>
  );
}

// ============================================
// Export Modal
// ============================================

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  exportType: ExportType;
  data: Record<string, unknown>;
  title?: string;
}

export function ExportModal({
  isOpen,
  onClose,
  exportType,
  data,
  title,
}: ExportModalProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('csv');
  const [isExporting, setIsExporting] = useState(false);

  if (!isOpen) return null;

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const endpoint = getExportEndpoint(exportType);
      const response = await api.post(endpoint, data, {
        params: { format: selectedFormat },
        responseType: 'blob',
      });

      const contentDisposition = response.headers['content-disposition'];
      let filename = `${exportType}_export.${selectedFormat}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=(.+)/);
        if (match) filename = match[1];
      }

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      onClose();
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-md mx-4 bg-slate-900 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Download className="h-5 w-5 text-emerald-400" />
            {title || 'Export Data'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Format</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                className={cn(
                  'p-3 rounded-lg border text-left transition-colors',
                  selectedFormat === 'csv'
                    ? 'border-emerald-600 bg-emerald-600/10'
                    : 'border-slate-700 hover:border-slate-600'
                )}
                onClick={() => setSelectedFormat('csv')}
              >
                <FileSpreadsheet className="h-5 w-5 text-emerald-400 mb-1" />
                <p className="text-sm font-medium text-white">CSV</p>
                <p className="text-xs text-slate-400">For Excel, Sheets</p>
              </button>
              <button
                className={cn(
                  'p-3 rounded-lg border text-left transition-colors',
                  selectedFormat === 'json'
                    ? 'border-emerald-600 bg-emerald-600/10'
                    : 'border-slate-700 hover:border-slate-600'
                )}
                onClick={() => setSelectedFormat('json')}
              >
                <FileJson className="h-5 w-5 text-blue-400 mb-1" />
                <p className="text-sm font-medium text-white">JSON</p>
                <p className="text-xs text-slate-400">For developers</p>
              </button>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="outline"
              className="flex-1 border-slate-700 text-slate-300"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              className="flex-1 bg-emerald-600 hover:bg-emerald-500"
              onClick={handleExport}
              isLoading={isExporting}
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================
// Helpers
// ============================================

function getExportEndpoint(exportType: ExportType): string {
  const endpoints: Record<ExportType, string> = {
    portfolio: '/export/portfolio',
    watchlist: '/export/watchlist',
    screening_results: '/export/screening-results',
    tax_report: '/export/tax-report',
    trade_journal: '/export/trade-journal',
    stock_analysis: '/export/stock-analysis',
  };
  return endpoints[exportType];
}

