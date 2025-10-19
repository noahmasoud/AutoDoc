import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { RulesComponent } from './rules.component';

@NgModule({
  declarations: [RulesComponent],
  imports: [
    CommonModule,
    RouterModule.forChild([
      { path: '', component: RulesComponent }
    ])
  ]
})
export class RulesModule {}
