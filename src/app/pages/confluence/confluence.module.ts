import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ConfluenceComponent } from './confluence.component';

@NgModule({
  declarations: [ConfluenceComponent],
  imports: [
    CommonModule,
    RouterModule.forChild([
      { path: '', component: ConfluenceComponent }
    ])
  ]
})
export class ConfluenceModule {}
