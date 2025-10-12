import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AutoDocComponent } from './auto-doc.component';

@NgModule({
  declarations: [AutoDocComponent],
  imports: [
    CommonModule,
    RouterModule.forChild([
      { path: '', component: AutoDocComponent }
    ])
  ]
})
export class AutoDocModule {}
