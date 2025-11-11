import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatChipsModule } from '@angular/material/chips';
import { AnalyzerFindingsComponent } from './analyzer-findings.component';

@NgModule({
  declarations: [AnalyzerFindingsComponent],
  imports: [CommonModule, MatChipsModule],
  exports: [AnalyzerFindingsComponent],
})
export class AnalyzerFindingsModule {}

