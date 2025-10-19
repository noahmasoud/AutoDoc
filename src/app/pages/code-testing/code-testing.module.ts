import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CodeTestingComponent } from './code-testing.component';

@NgModule({
  declarations: [CodeTestingComponent],
  imports: [
    CommonModule,
    RouterModule.forChild([
      { path: '', component: CodeTestingComponent }
    ])
  ]
})
export class CodeTestingModule {}
