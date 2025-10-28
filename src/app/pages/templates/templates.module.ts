import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { TemplatesComponent } from './templates.component';

@NgModule({
  declarations: [TemplatesComponent],
  imports: [
    CommonModule,
    RouterModule.forChild([
      { path: '', component: TemplatesComponent }
    ])
  ]
})
export class TemplatesModule {}
