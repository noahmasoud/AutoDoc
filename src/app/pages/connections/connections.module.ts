import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { ConnectionsComponent } from './connections.component';

@NgModule({
  imports: [
    ConnectionsComponent, // Import standalone component
    RouterModule.forChild([
      { path: '', component: ConnectionsComponent }
    ])
  ]
})
export class ConnectionsModule {}
