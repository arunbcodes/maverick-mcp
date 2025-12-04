'use client';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, TrendingUp, Zap } from 'lucide-react';

export default function ScreenerPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Stock Screener</h1>
        <p className="text-slate-400 mt-1">
          Find stocks matching your criteria
        </p>
      </div>

      {/* Search */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Search stocks by ticker or name..."
                className="pl-10 bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <Button className="bg-emerald-600 hover:bg-emerald-500 text-white">
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Quick Screens */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="bg-slate-900/50 border-slate-800 hover:border-emerald-800/50 transition-colors cursor-pointer">
          <CardHeader>
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-emerald-600/20">
                <Zap className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <CardTitle className="text-white text-lg">
                  Maverick Picks
                </CardTitle>
                <CardDescription className="text-slate-400">
                  High momentum opportunities
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800 hover:border-emerald-800/50 transition-colors cursor-pointer">
          <CardHeader>
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-emerald-600/20">
                <TrendingUp className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <CardTitle className="text-white text-lg">
                  Breakout Stocks
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Breaking key resistance levels
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800 hover:border-emerald-800/50 transition-colors cursor-pointer">
          <CardHeader>
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-emerald-600/20">
                <Search className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <CardTitle className="text-white text-lg">
                  Custom Screen
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Build your own criteria
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Results Placeholder */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">Screening Results</CardTitle>
          <CardDescription className="text-slate-400">
            Select a screener or search to see results
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Search className="h-12 w-12 text-slate-600 mb-4" />
            <p className="text-slate-400">
              Use the search bar or select a quick screen to get started
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

