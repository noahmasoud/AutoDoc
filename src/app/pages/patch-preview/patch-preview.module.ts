import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

// Angular Material modules
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatDialogModule } from '@angular/material/dialog';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';

import { PatchPreviewComponent } from './patch-preview.component';

@NgModule({
  declarations: [PatchPreviewComponent],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild([
      { path: '', component: PatchPreviewComponent }
    ]),
    // Angular Material
    MatCardModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatDialogModule,
    MatChipsModule,
    MatExpansionModule,
    MatSelectModule,
    MatTooltipModule,
  ]
})
export class PatchPreviewModule {}

