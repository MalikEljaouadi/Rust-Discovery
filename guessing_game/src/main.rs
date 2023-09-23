use rand::Rng;
use std::cmp::Ordering;
use std::io;

fn main() {
    println!("this is the Guess number game!");

    loop {
        println!("input the number");
        let secret_number = rand::thread_rng().gen_range(1..101);
        
        println!("The secret_number is: {secret_number}");
        
        let mut guess = String::new();
        io::stdin()
            .read_line(&mut guess)
            .expect("Error while reading input number");

        let guess: u32 = match guess.trim().parse(){
            Ok(num) => num,
            Err(_) => {
                println!("unvalid input");
                continue;
            },
        };

        println!("You guessed: {guess}");

        match guess.cmp(&secret_number) {
            Ordering::Less => println!("too small"),
            Ordering::Equal => {
                println!("You win!");
                break;
            },
            Ordering::Greater => println!("too big"),
        }
        
    }
}
