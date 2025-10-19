import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ConnectionsComponent } from './connections.component';

@NgModule({
  declarations: [ConnectionsComponent],
  imports: [
    CommonModule,
    RouterModule.forChild([
      { path: '', component: ConnectionsComponent }
    ])
  ]
})
export class ConnectionsModule {}
