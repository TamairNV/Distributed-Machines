import {Component, inject, signal} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {Router, RouterLink} from '@angular/router';

@Component({
  selector: 'app-create-account',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './create_account.html',
})
export class CreateAccountComponent {
  http = inject(HttpClient);
  router = inject(Router);

  userName = '';
  userPasskey = '';
  userNameTaken = signal('');
  isLoading = false;
  createUser() {
    if (this.isLoading) {
      return;
    }
    this.isLoading = true;
    this.userNameTaken.set('');

    const newUser = { name: this.userName, passkey: this.userPasskey };

    this.http.post('/api/create-user', newUser,
      { withCredentials: true })
      .subscribe({
        next: (response: any) => {
          this.isLoading = false;
          console.log(response,response.received)
          if (response.received == "Taken") {
            this.userNameTaken.set('Username is taken. Please try another one.');
          } else {
            this.router.navigate(['/login']).then(r => {});
            console.log('User created successfully!', response);
          }
        },
        error: (err) => {
          this.isLoading = false;
          this.userNameTaken.set('Username is taken. Please try another one.');
          console.error('Flask request failed:', err);
        }
      });
  }
}
