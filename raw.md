## Raw transcript of the hackathon information
You: Uh, we're a company that builds AI solutions and automations for long-forms in the U.S., specifically personal injury law firms. I'm going to explain a bit of what that is in a minute, but today it's about seeing how far you can take AI in just 6 hours to build the most complete product possible, and you're going to see that it's really with less technical and other hackathons that we've hosted.
You:  But the idea today is to see how far you can take AI. So the goal of today is just to have fun, build something cool, and get to know people.
You:  So, the reason you're here today: the prices speak for themselves. Uh, the first 3 places are going to get the price pools that you can see on the screen.
You:  Also, another reason that you're here today is that everything that you're building is going to be 100% yours, so feel free to add it to your portfolio, ship it, do whatever you want with it. And lastly, we're also going to have trial attorneys and top AI builders as part of the judges.
You:  They're going to be judging your solutions today. Trial attorneys are the ones that would actually be using this solution, so they're the ones that are going to be seeing how useful it would be for them on a day-to-day run.
You:  Plus, everyone here gets access to tonight's private concert, so despite the prices and everything else, we really want you to take today as an opportunity to just network, build something really fun, and attend one of the biggest law conferences in the U.S. So, before we get started with the actual challenge and the explanation, I really want to thank our sponsors and judges for making this day possible.
You:  We are extremely excited to have you here today. And we also want to help our recruiters, Austin and Florian, for making the fact that you're here possible as well and helping recruit these amazing builders in the room.
You:  So a big round of applause for them.
You:  Okay, so as you may know, today we're going to be solving a real industry problem that we meet here in our time in the industry. But this is pretty much all law that you need in order to solve the challenge for today.
You:  This is what personal injury is in law. Someone gets hurt, right?
You:  Usually it's in a car crash. And the victim will hire an attorney.
You:  Now, the attorney only will get paid if the client and the attorney win that case, right? During that case, obviously there's an injured party that needs medical treatment.
You:  So during that time, medical providers treat on a promise. What does that mean?
You:  That the client doesn't go and pay for the treatment right away, but they get a promise that when they settle the case, so when they get the money from that case, they will be paid back out of that money, right? Now, a case can take years to settle, and all cases can have multiple medical providers, right?
You:  So records start to pile up. The file starts to grow.
You:  You have notes. You have records.
You:  You have bills. And communication between the law firm and the medical providers can start getting a little bit clunky, right?
You:  So we have the two sides. We have, on the one side, the firm, and on the other side, the medical provider that is treating the client on what we call a lien, which is this promise, right?
You:  One small tip is that bills, so these liens, these promises that the medical providers are getting, are usually negotiated when they get their money back, so when the case settles. So that the client can take more money home, right?
You:  Because when we settle a case, part goes to the attorney, part goes to the medical providers, and what's left goes to the actual client. So the injured party.
You:  We try to negotiate those prices down so the client can take more money home.
You: About keeping the information off a case, so keeping any fields that we need, any notes, any documents, but nowadays we believe that there's no system that can actually display that information in a way that is useful to get access to people with a case weekly, and to also allow for the visibility of those medical providers. Just for the ones that are taking pictures, the way that we're going to share the slides after the presentation.
You:  So, capturing the case or the information of the case is a problem that's already going to be solved for you today. We're going to hand you over a matter, so a real case with all the information that you're going to need, the challenge for today is actually digesting it, so turning it into a live dashboard that can help get access to people in just 90 seconds by looking at it, right?
You:  Here's an example of the current dashboard of a case management system that exists today. It's the one that we're going to be working with as well.
You:  I'm going to explain in just a minute why we think this dashboard is really good but not good enough.
You:  So, as we said, we have two sides: on one side we have the actual law firm, and the other side we have the provider. Right now our dashboards that exist for the actual law firm, there's nothing that exists for the actual medical provider to see where a case stands.
You:  And they're interested in it, right, because they're getting the money from that case. So they want to be seeing how much money do we expect to be getting from the case, where the case stands, how much longer do we have to wait for example, right?
You:  So the goal of the challenge today is has two parts, right? First of all, the dashboard that we're going to be building has to be able to get the internal team members of a firm access to people with a case as fast as possible, right, by just looking at this I need to be able to know who the person is, what happened to them, what are the injuries, what is the last thing that happened to the case, anything that I need to know, whether it's my first time viewing the case or if I'm just trying to get up to speed from seeing it from just a couple weeks ago, right?
You:  And on the other hand, we're trying to improve the communication and visibility of the case with the medical providers that are involved in the client's treatment.
You:  So something important about this is that there's no actual checklist of features that we're going to be providing part of the challenge is to take these two sentences and understanding what does this mean to you, and what are the features that you want to be implementing in order to solve for these two problems, right?
You:  Now, that said, this is a bunch of brainstorming a bunch of ideas and codes that we heard from the industry of problems that they mentioned that they have, and that they could be solved by this solution, right? Don't worry, the people on the back, I know it's a bit tiny, we're going to be providing the slides in just a minute.
You:  So, the idea today is that you're able to take some of these quotes, do your own research, ask the attorneys that are going to be in the room in and out during the day, and understand what is the biggest priority that you should be implementing on your product today. Obviously, this is a lot of stuff, so we're not expecting all of you to be able to tackle each one of these problems.
You:  Part of the challenge is to understand what to prioritize and what to build as a feature in order to solve one of these problems, right?
You:  So, an important piece to share is that a provider, a medical provider, the one that is treating the client, is not part of the firm, right? So the solution that we're going to be building for the law firm itself should not be the same that we're going to be building for the medical provider.
You:  We don't want to be sharing all the information about the case to all the medical providers, right? Some really simple ideas of what we want to be sharing, for example, the status of the case, where the case stands so that the medical providers can see how long it might take for the case to settle still, and the bills and records, right?
You:  What this means is how much we have to pay you, and what for, right? Things that we obviously don't want to be sharing is case strategy, that lives in the same case management system, and anything that is confidential or critical to a client, that is not relevant to that specific provider, right?
You:  Now, part of the challenge as well is that not all attorneys will choose to share the same information and to each provider. We might have a more firm relationship with some providers, for others we might not want to share all the same pieces of information, and the different firms can choose to maybe share some piece of information and some other not, right?
You:  If you're not sure where the line is, again, we're going to have attorneys in the room in and out during the entire day, so feel free to grab them, stop them, and make any questions that you need in order to make this product as good as possible. We have any attorneys in the room right now?
You:  Here you go.
You:  Take a look at his face. Feel free to grab him, ask all your questions.
You:  Sorry about that.
You:  Just a few questions. You're going to have a lot of attorneys in the room, so try not to stop them too much.
You:  But feel free to ask any questions, and we're going to have a bunch of people right here, so you can ask your questions whenever.
You:  So, this is what I was talking about before. This is an example of a good dashboard but not good enough.
You:  But it's simply looking at this, you can see that it has some good KPIs, it has custom fields, contact details, some information that can be pretty useful, but this is not enough for someone that has never looked at the case before, to simply look at this and understand what is going on, what happened, what is this case about, right?
You:  You will still have to go to the different tabs, you have activities, communications, documents, all the information actually lives in the case management system, but it might not be the best way to display it, right?
You:  Another example from another case management system, again, good dashboard, we have some KPIs, we have the workers of the case, some case tasks, but again, this simply looking at this, I'm not sure what exactly happened, right?
You:  Lastly, this is a CRM, same thing, we have, for example, the stage of the matter, some upcoming activity, but again, this is not something that I would just be able to look at and see what is happening with the case, right?
You:  So, where are you going to be starting?
You:  You're going to be creOf providing, um, will be input, right?
You:  Again, no card needed; it's free. It just takes a couple minutes.
You:  Now, if anyone is on Teams, you will just need one account per team; you just don't need to create one per person, right?
You:  And it's really simple: just follow the steps. In order to create the free account, then connect it to this app that is going to input the information in.
You:  So, what you're going to be getting in this module is all the real information that an actual matter in real life would have, as we said before, contacts, custom fields, notes, case expenses, communication, and everything else that a real case would actually have, and the challenge is to take all of that information and display it in the best way possible to help any internal members get up to speed, but also create that visibility for medical providers.
You:  So, rules: barely any. Only rules is Teams up to 3 people.
You:  Solo teams are fine; you're just going to tell us whatever you submit. Any stack, any tools are fine.
You:  Again, AI-assisted coding is the point of this hackathon; it's not a loophole. And again, you own everything that you're going to be building today.
You:  We only get to display the video that you're going to be submitting and showcase it today. Everyone's going to build on one matter; this matter is going to be provided called subpoena.
You:  The idea is that your build reads off this matter and is able to display it. Now, second rule: we are going to read the repository.
You:  That you sent over to us, so please make sure that nothing's hard-coded to the data, and it's actually reading the data from the code. From the case management system.
You:  And lastly, the one rule that we do have is that Clio should only be your input. You shouldn't be making any API calls to write to Clio manage.
You:  If you need any databases, please bring your own. The idea is that this kind of a solution should never be writing into the case management system of the firmware.
You: The judges want to be once are evaluating this, so anything that you want to tell them, any differentiators, why you chose the features that you did, anything at all that you want them to know, and you're going to have the opportunity to tell them in the submission. And lastly, this is completely optional but if you want to create an actual live link or an install path, you're going to be able to submit it in this form.
You:  Um, now, localhost can completely win here; this is not a requirement. You have 6 hours, so the idea is that you choose your battles, basically.
You:  What's the best path? Would you rather add a new feature, or would you rather have an install path, right?
You:  Okay, there's one necessity to actually have an install path. Now, this is something that I want to be really clear on: the deadline is 4:00 p.
You: m. hard, close. The reason for this is that the time that we have to evaluate is really time-sensitive, so we're not going to be looking at any solutions at 4:01.
You:  So please take that into account when you're going to submit the form. Try to have everything already ready by 3:30.
You:  The form might take about 10 minutes to submit. If you want to add a little bit more of your work, please take that into account again when submitting the solution.
You:  Again, really hard deadline is 4:00. That is when we start evaluating, so anything that comes after that, we won't even see, right?
You:  So, what happens after you submit? Again, 4:00, you submit your solution.
You:  We have an hour to screen through all of you guys' solutions. I'm going to be picking the top 7.
You:  The top 7 are going to go to the judges. And the top 7 teams are solo groups are going to be presenting your video to the judges.
You:  Um, the judges are going to deliberate, and they're going to pick the top 3 ranked. So for a second and third, we're not going to reveal just yet the order.
You:  The top 3 and everyone else that wants to join, we're going to go to the main stage at 7:00. And one of our team members, Santi, is going to present the top 3 solutions in the main stage for all of the attendees to see.
You:  Now, something that we want to clarify here: getting to the top 7 is one on the code, right? Because we're going to evaluating the features as well as the repository.
You:  But winning or being part of the top 3 is one on stage, right? On showing to the judges, convincing them why is your solution the best one, why did you choose the features that you did.
You:  And pretty much getting to the top 3 is about convincing them why your solution is the best.
You:  So this is pretty much what I just talked about, which is half the schedule of the entire day. The point of this slide is just to tell you that we have lunch included.
You:  At noon, Anna right there in the back is going to be telling you exactly where the room is, and we're going to remind you just a little bit, a few minutes earlier. Now, we do recommend that you go there around 11:30 if you want to avoid the queues a little bit, and you can come back as quickly as possible to work on your solutions.
You:  But don't worry, we're going to remind you when we're a little bit closer to that time. Um, and again, after 7:00 p.
You: m., after we present all the solutions, you are all welcome to join the private concert that's going to be in the main stage.
You:  So, that's pretty much it. You have the Wi-Fi.
You:  Network and password in here. You're going to be able to access the slides on the QR code above.
You:  And the other QR code is to submit the app, so it's going to be the fill-out form for you to submit at 4:00. Um, so feel free to start building those solutions.
You:  Welcome, everybody, and good luck.
You:  Any questions?
You:  Perfect.
You:  Uh, yes?
You:  Go ahead.
You:  The Wi-Fi is not working.
You:  Oh, we have another Wi-Fi.
You:  We have another Wi-Fi, just in case. I will add it to the slide in just a second.
You:  Um, we are working with IT, I believe, to have to have the connection. We start as quickly as possible, but feel free to switch between those two Wi-F
